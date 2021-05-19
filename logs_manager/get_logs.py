import datetime
import logging
import re
import sys
import time
import traceback
import socket
from functools import wraps

import example_email
from example_db.conexao import *

LOG_TABLE = "LogPython"

class pseudoFile():
    def __init__(self):
        self.text = ''

    def write(self, data):
        if data and len(data.strip()) > 54 and data.strip()[55:] not in ("- [", " ", "-", "- ", "- ]", "]", "[" "-"):
            if data.find("<strong>") != -1:
                self.text += data.strip()[55:] + '<br>'
            else:
                self.text += data.strip() + '<br>'

    def readlines(self):
        return self.text


class logs(object):
    def __init__(self, func_name):
        self.past_stdout = sys.stdout
        sys.stdout = self
        self.scope = func_name
        self.file_name = pseudoFile()
        self.status = '(ERRO)'


        # criando e configurando o logger
        self.logger_exc = logging.getLogger(self.scope)
        formatter = logging.Formatter(fmt='<font color="silver">%(asctime)s :: - %(message)s',
                                      datefmt='%d/%m/%Y - %H:%M:%S</font>', style='%')
        string_log = logging.StreamHandler(self.file_name)
        string_log.setFormatter(formatter)
        self.logger_exc.addHandler(string_log)
        self.logger_exc.setLevel(10)
        self.start_date = datetime.datetime.now()

    def end(self, scope):
        hostname = socket.gethostname()
        sys.stdout = self.past_stdout
        msg = f'<div style="text-align:center"><h2><strong><font color="darkblue">Rodando em {hostname}: </strong>{scope}</font></h2><hr></div>"'
        example_email.exchange_mail_api.enviar_email(assunto=f'Log de execução do {self.scope} {self.status}',
                                                  mensagem=msg + self.get_log_content(),
                                                  destinatarios=example_email.DEVELOPERS_GROUP,
                                                  conta=example_email.sender.ContaExample(),
                                                  salva_envio=False)

    def get_log_content(self):
        return self.file_name.readlines()

    def flush(self):
        pass

    def tira_timestamp(self):
        data = self.file_name.readlines().split("<br>")
        timestampless_data = []
        for d in data[:-2]:
            d = d.strip()[55:]
            timestampless_data.append(d)
        return timestampless_data

    def salva_banco(self, dur, tb=None):
        """ NOME_SCRIPT // HORA_INICIO // DURACAO // ERROS // TRACEBACK """

        con = get_conn()
        cur = con.cursor()
        erros = 1 if self.status.__eq__('(ERRO)') else 0
        if tb:
            tb = (tb[tb.find('kwargs') + 10:])

        sql_insert = f"INSERT INTO {Conexao.nome_banco()}.{SCHEMA_DBO}.{LOG_TABLE} " \
                     f"(nome_script, hora_inicio, duracao, erros, traceback) " \
                     f"VALUES (?, ?, ?, ?, ?)"

        cur.execute(sql_insert, [self.scope, self.start_date, dur, erros, tb])
        cur.commit()

    def write(self, data):
        self.logger_exc.info(data)
        if self.past_stdout is not None:
            self.past_stdout.write(clean_html(data))


def clean_html(text):
    return re.sub('<[^<]+?>', '', text)


def logger(func):
    # esse decorator de functools ajuda a consertar a referencia a nomes fora de scope
    @wraps(func)
    def func_wrapper(*args, **kwargs):
        try:
            start = time.time()
            logger = logs(func.__name__)
            xxx = func.__code__.co_filename.split('/')[-1]
            xxx = xxx.split('\\')[-1]
            xxx += ' - ' + func.__name__
        except:
            scope = func.__code__.co_filename.split("/")[-1].split('\\')[-1] + ": " + func.__name__
            example_email.exchange_mail_api.enviar_email(assunto='Erro ao criar o log de execução (ERRO FATAL) ' \
                                                              f'{scope}',
                                                      mensagem="O log não pôde ser criado por algum motivo.",
                                                      destinatarios=example_email.DEVELOPERS_GROUP,
                                                      conta=example_email.sender.ContaExample(),
                                                      salva_envio=False)
        else:
            tb = None
            try:
                print(start)
                returned = func(*args, **kwargs)

                if returned:
                    logger.write(str(returned))

            except Exception:
                try:
                    returned = func(*args, **kwargs)

                    if returned:
                        logger.write(str(returned))
                except:
                    tb = traceback.format_exc()
                    if tb:
                        logger.status = '(ERRO)'
                        logger.write('<font color="red"><strong><hr><h3><center>'
                                     '-_-_-_-_-_-_-_-_-_ERROR TRACEBACK_-_-_-_-_-_-_-_-_-'
                                     '</h3></strong></center>')
                        logger.write(tb[tb.find('kwargs') + 10:].replace("\n", "<br>") + '</font><br><br>')
                else:
                    logger.write("O script se recuperou de um erro automaticamente.")
                    logger.status = '(SUCESSO)'
            else:
                logger.status = '(SUCESSO)'

            finally:
                end = time.time()
                print('     ')
                hours, rem = divmod(end - start, 3600)
                minutes, seconds = divmod(rem, 60)
                print("<center><strong>"
                      "Total elapsed time: "
                      "{:0>2} horas, {:0>2} minutos e {:.3f} segundos "
                      "</strong></center>".format(int(hours), int(minutes), seconds))

                try:
                    logger.salva_banco(tb=tb, dur=f"{int(hours)}:{int(minutes)}:"+'{:.2f}'.format(seconds))
                except:
                    tb = traceback.print_exc()
                    logger.write("Não foi possivel inserir este log no banco de dados:")
                    if tb:
                        logger.write(tb[tb.find('kwargs') + 10:])

                logger.end(xxx)
                logger = logs(func.__name__)

                try:
                    return returned
                except:
                    pass

    return func_wrapper

# LOGS MANAGER EXAMPLE

**logs_manager** - Um decorator que pode ser utilizado em qualquer função genérica. Colocando o decorator "@logger" em qualquer função
permite que o logs_manager duplique as saídas de stdout da função. 
Um deles vai para onde deveria ir segundo o programa normal, o outro duplicado
é colocado em um texto que é depois enviado para o email do grupo de desenvolvedores com formatação HTML

=========================================
Módulos de carga de datos de EXPA a PODIO
=========================================

AVISO
------
Este módulo se va a generalizar/deprecar para correr los scripts a yellowCrons. El procedimiento está aún por definir

Introducción
-------------

Este módulo fue diseñado para organizar y centralizar todos los scripts que requieren cargar información de EXPA y subirla a una aplicación de PODIO, y configurarlos de tal manera que si es necesario dichos scripts puedan ser corridos periódicamente (diariamente por lo general) y así hacer operaciones diarias de carga tales como quienes se están registrando, están siendo contactados o entrevistados, están en approved, entre otras. Ya existen algunos ejemplos de cómo funcionan esos scripts, pero para hacer más es recomendable estudiar el funcionamiento de los módulos de EXPA y PODIO, y las APIs en las cuales estos se basan

Instalación
-----------
Agregar el módulo (``podioExpaLoaders``) a ``INSTALLED_APPS`` dentro del archivo ``settings.py``. Esto asegura que los `management commands <https://docs.djangoproject.com/en/1.9/howto/custom-management-commands/>`_ sean detectados por el comando ``management.py`` y puedan ser corridos desde la línea de comandos de Linux, o como un cronjob


Dependencias
------------
Este módulo requiere la instalación y configuración previa de los módulos ``django_expa`` y ``django_podio``
  - django_expa: https://github.com/camiloforero/django_expa
  - django_podio: https://github.com/camiloforero/django_podio

La información sobre la instalación y configuración de dichos módulos se puede encontrar en sus readme respectivos.

Configuración
-------------

La aplicación actualmente está configurada para correr diariamente el método `mc_daily_load encontrado en el módulo mc_scripts.  <https://github.com/camiloforero/podioExpaLoaders/blob/master/mc_scripts.py>`_ Este es el método que hay que modificar para definir lo que se busca ejecutar diariamente.

Funcionamiento
--------------

La base del funcionamiento de esta aplicación es en la creación de un management command de Django, llamado mc_daily. El código se puede encontrar `en este link <https://github.com/camiloforero/podioExpaLoaders/blob/master/management/commands/mc_daily.py>`_
, básicamente lo único que hace es llamar la función mc_daily_load dentro del módulo mc_scripts. Este paso es necesario para poder llamar ``$ python manage.py mc_daily``, y permite que sea utilizado también dentro del cronjob. Más información sobre los management commands de django se puede encontrar `en este link. <https://docs.djangoproject.com/en/1.9/howto/custom-management-commands/>`_

Una vez está bien configurado, es necesario configurar el cronjob. A continuación una explicación de cómo podría funcionar uno

.. code-block::

  PYTHONIOENCODING=utf8
  30 0 * * * /var/www/yellowPlatform/yellowEnv/bin/python /var/www/yellowPlatform/manage.py andes_daily >> /tmp/cronlog_expa_podio_andes.txt 2>&1

La directiva ``PYTHONIOENCODING=utf8`` asegura que no haya errores de ejecución en caso que algún script tenga tildes. El ``30 0 * * *`` quiere decir que este script corre a las 0:30 horas todos los días (para más información `revisar el funcionamiento de un Cron <https://en.wikipedia.org/wiki/Cron>`_
). ``/var/www/yellowPlatform/yellowEnv/bin/python`` le dice al cron que no utilice el ejecutable de python del sistema, sino el ejecutable del entorno virtual del proyecto (Es altamente recomendable que cada proyecto de django tenga su propio entorno virtual, información acerca de cómo configurar uno `se puede encontrar aquí <https://www.digitalocean.com/community/tutorials/common-python-tools-using-virtualenv-installing-with-pip-and-managing-packages>`_
). ``/var/www/yellowPlatform/manage.py andes_daily`` dice que ejecute el management command llamado ``andes_daily``, en el caso del MC sería ``/var/www/mc_apps/manage.py mc_daily``. Por último, ``>> /tmp/cronlog_expa_podio_andes.txt 2>&1`` le dice al cron que redirija ``stdout`` (generalmente cuando utilizo el comando ``print``) y ``stderr`` (los errores que pueden haber en tiempo de ejecución) al archivo txt que ahí se indica. Es recomendable leer este log periodicamente para detectar posibles errores


Tips
----

Recomendación de por qué estos scripts diarios deberían correr a las 12:30, GMT


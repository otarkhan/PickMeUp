gunicorn -w 3 -b 0.0.0.0:80 --chdir /root/PickMeUp_Server/ pickmeup:app

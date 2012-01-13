nose:
	nosetests --nologcapture --with-gae --gae-lib-root=${GAE_PYTHON_SDK_HOME} --gae-application=www --where test
	
serve:
	python ${GAE_PYTHON_SDK_HOME}/dev_appserver.py --datastore_path=./data/default.datastore --high_replication --port 8083 --address=0.0.0.0 www
	

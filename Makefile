container:
	docker build -t hudl/infrakit .

host:
	cp wrapper/host /usr/local/bin/infrakit
	chmod +x /usr/local/bin/infrakit

infrakit: container host
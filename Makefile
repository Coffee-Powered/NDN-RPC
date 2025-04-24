setup: Vagrant/Vagrantfile
	git pull origin
	cd Vagrant && vagrant up && vagrant ssh-config > .ssh_config
	rsync -avH -e "ssh -F ./Vagrant/.ssh_config" default:~/testbed/ ./testbed/	
	cd ..

start:
	cd Vagrant && vagrant ssh

stop:
	cd Vagrant && vagrant halt

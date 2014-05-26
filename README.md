GitHub Hanger
=============
A Python-based web-service for GitHub web-hooks

## Installation and Configuration
### Setting up the Web-server

#### Create folders for our app
```bash
mkdir /var/www/ghservice/
mkdir /var/www/pvtdir/
```

#### Change ownership of folders
Change the owner of the newly created folders to the user and group of the Apache web-server (www-data). This is better than modifying the user/group of the running Apache process from `/etc/apache2/envvars`

```bash
chown -R www-data:www-data /var/www/ghservice/
chown -R www-data:www-data /var/www/pvtdir/
```

#### Web-server Dependencies
```bash
sudo apt-get update && sudo apt-get upgrade
sudo apt-get install apache2
sudo apt-get install libapache2-mod-wsgi
```
The web-service currently depends on WSGI, that's why we install mod-wsgi.

#### Web-server Configuration

1. Stop the Apache service:

    ```bash
    sudo service apache2 stop
    ```
2. Enable execution of CGI scripts, by adding the following lines to `/etc/apache2/apache2.conf`

    ```apache
    <Directory /var/www/ghservice/>
      Options +ExecCGI
    </Directory>
    ```

3. Set WSGI as the handler for Python scripts, by adding the following lines to `/etc/apache2/mods-available/wsgi.conf`:

    ```apache
    # Handle all .py files with mod_wsgi
    <FilesMatch ".+\.py$">
    SetHandler wsgi-script
    </FilesMatch>

    # Deny access to compiled binaries
    # You should not serve these to anyone
    <FilesMatch ".+\.py(c|o)$">
    Order Deny,Allow
    Deny from all
    </FilesMatch>
    ```
4. Restart Apache service:

    ```bash
    sudo service apache2 start
    ```

#### Python Modules
```bash
sudo apt-get install python-setuptools
sudo easy_install pip
sudo pip install configobj
sudo pip install pygithub
```

#### Deployment

Deploy the web-service to `/var/www/ghservice/`. Make sure they have the right owner/group set.

### Linters' Configuration

1. Upload linters' binaries to the following path: `/home/symbyo/linters/`
2. Create a symbolic link to the linter binary as follows:

    ```bash
    ln -s `/usr/%BINARY%`  `/home/symbyo/linters/%BINARY%`
    ```
3. Add linters' wrappers to `/var/www/ghservice/linters/`. Make sure they have the right owner/group set.
4. Add linter wrapper config to the configuration file `/var/www/ghservice/config.ini` as subsection under the `[Linters]` section as follows:

    ```INI
    [[%LINTER_NAME%]]
    wrapper_module = "%LINTER_WRAPPER_MODULE_NAME%"

    # You can also add a list for "include_patterns" or "ignore_patterns" here which are specific to your linter
    ```
5. Install linter specific dependencies.

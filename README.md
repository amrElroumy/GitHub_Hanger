GitHub Hanger
=============
A Python-based web-service for GitHub web-hooks

## Web-server Installation and Configuration
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

## Webhooks Configuration

In order to create a webhook and configure it to work with your service you could read this [GitHub guide on the subject](https://developer.github.com/webhooks/creating/) or simply follow the next steps.

**Requirements:** You need to have access to the settings panel of the repository you want to enable the webhooks for.

Steps:

1. Go to the settings panel of the repository
2. Jump to Webhooks and Services tab
3. In the Webhooks section, click add webhook.
4. Configure the webhook for your service:
    - Payload URL: Location where GitHub will send you the payload.. Should be a publicly accessible URL of the web-service. E.g. `http://127.0.0.1/service_directory/script.py`
    - Content type: "application/x-www-form-urlencoded"
    - Secret: Not currently used, but it is useful to identify that the payload is from GitHub and not from anyone else.
    - Event's selection: You get to choose which events you want to be notified with, or all the events, or only the push events. For more information check [this](https://developer.github.com/webhooks/#events)
    - Is Active: Check this box to activate the webhook
5. Click update the webhook to save your modifications.


A test payload ([Ping Event](https://developer.github.com/webhooks/#ping-event)) will be sent to the payload URL on creation of the webhook to make sure that everything is working. It should look something like this:
```json
{
  "zen": "Anything added dilutes everything else.",
  "hook_id": 2247556
}
```

All the delivered payloads are stored in the recent deliveries of the current webhook, you can easily view them and redeliver them for debugging purposes.
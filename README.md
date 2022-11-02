# Developer [![Coverage Status](https://coveralls.io/repos/github/tangb/cleepapp-developer/badge.svg?branch=master)](https://coveralls.io/github/tangb/cleepapp-developer?branch=master) [![Codacy Badge](https://app.codacy.com/project/badge/Grade/9f7643837f844164b846fd3970cb1633)](https://www.codacy.com/gh/CleepDevice/cleepapp-developer/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=CleepDevice/cleepapp-developer&amp;utm_campaign=Badge_Grade)

Developer application for Cleep

![](https://github.com/tangb/cleepapp-developer/raw/master/resources/background.jpg)

## Presentation

This application allows you to develop as easily as possible new applications in Cleep environement.

It installs [cleep-cli](https://github.com/tangb/cleep-cli) which is a dedicated cli that executes dedicated Cleep commands directly on device.

It allows to create new application, check your application code, execute unit tests...

Thanks to this cli and the developer application, you can develop remotely without connecting to the device.

## Features

### Developer helpers

* Create new application: it creates default application with default documentation config, base backend and frontend skeleton and default test file.
* Access to Cleep logs shortcut
* Gives links to best development practices: semver, changelog...

### Tests

This feature helps you running application unit tests displaying results. You can also view code coverage of latest run.

### Documentation

Documentation generation with output. It helps you fix warning or errors and preview generated documentation (in text format)

### Application build

It checks backend and frontend mandatory stuff and returns errors that need to be fixed and warnings. It also check version and changelog content.
The analyze report is displayed in developer page with all app informations helping you to check if your next release is ok for you.

Finally a build application button is available to create ready to publish archive. In the future, a publication button will be added to directly publish your application in Cleep market.

### Remote development

Please follow this [tutorial](https://github.com/tangb/cleep-cli#watch-usage) to configure VSCode to enable remote development. You can use another EDI as long as it allows to push changes to another host (ftp, sftp...).
Cleep-cli will check for changes on frontend or backend files and restart what is needed automatically.

You can also connect with ssh to the device and directly develop on the device. See [here](https://github.com/tangb/cleep-cli#local-developments) for more informations.

## How it works

Open developer config page clicking on open button in developer app tile. Create an app from developer helpers tab. Then select the app you want to analyze.

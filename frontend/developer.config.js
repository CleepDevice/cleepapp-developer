/**
 * Developer configuration component
 * Helps developer to analyze and publish module to cleep store
 */
angular
.module('Cleep')
.directive('developerConfigComponent', ['$rootScope', 'toastService', 'cleepService', 'developerService', 'systemService', '$timeout', '$sce', '$location', '$q', '$mdDialog', '$window',
function($rootScope, toast, cleepService, developerService, systemService, $timeout, $sce, $location, $q, $mdDialog, $window) {

    // konami code: ssuperr

    var developerController = ['$scope', function($scope) {
        var self = this;
        self.developerService = developerService;
        self.config = {
            moduleInDev: null
        };
        self.selectedModule = null;
        self.modules = [];
        self.deviceIp = '0.0.0.0';
        self.checkData = null;
        self.selectedNav = 'buildmodule';
        self.selectedMainNav = 'devtools';
        self.newApplicationName = '';
        self.loading = false;
        self.analyzeError = null;
        self.remotedevUuid = null;
        self.cleepService = cleepService;
        self.logButtons = [];
        self.mdiUrl = '<a href=\"https://pictogrammers.com/library/mdi/\" target=\"_blank\">MaterialDesignIcons.com</a>';
        self.semverUrl = '<a href="https://semver.org/" target="_blank">https://semver.org/</a>';
        self.changelogUrl = '<a href="https://keepachangelog.com/" target="_blank">https://keepachangelog.com/</a>';
        self.testUrl = '<a href="https://pylint.org/" target="_blank">https://pylint.org/</a>';
        self.descUrl = '<a href="https://github.com/CleepDevice/cleepapp-developer/wiki/desc.json" target="_blank">https://github.com/CleepDevice/cleepapp-developer/wiki/desc.json</a>';
        self.docstringUrl = '<a href="https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html" target="_blank">Google docstring</a>';
        self.testsOutput = undefined;
        self.docsOutput = undefined;
        self.isDocsHtml = false;
        self.breakingChanges = undefined;

        /**
         * Init controller
         */
        self.$onInit = function() {
            self.logButtons = [
                {
                    label: 'Open logs',
                    icon: 'open-in-new',
                    click: self.openLogs,
                },
                {
                    label: 'Clear log file',
                    icon: 'delete',
                    click: self.clearLogs,
                    style: 'md-accent md-raised',
                },
            ];

			// set remotedev device
            self.setRemotedevDevice();
            
            // get device ip
            self.deviceIp = $location.host();

            // load module configuration
            cleepService.getModuleConfig('developer')
                .then(function(config) {
                    self.setConfig(config);

                    // get list of module names
                    self.modules = self.__modulesList(false);

                    // make sure god mode wasn't enabled before
                    if( self.config.moduleInDev && self.modules.indexOf(self.config.moduleInDev)===-1 ) {
                        self.modules = self.__modulesList(true);
                    }
                });
        };

        /**
         * Load modules that can be developed
         */
        self.__modulesList = function(all) {
            if( all===undefined ) {
                all = false;
            }

            var temp = [];
            for( var module in cleepService.modules ) {
                if( !all ) {
                    if( cleepService.modules[module].core===true || module==='developer' ) {
                        // core module, drop it
                        continue;
                    }
                }
    
                // append module name
                temp.push(module);
            }
            return temp.sort();
        };

        /**
         * Dummy click for line hover
         */
        self.dummyClick = function() {};

        /**
         * Godmode
         */
        self.godMode = function() {
            toast.info('God mode activated, all applications are available in list');
            self.modules = self.__modulesList(true);
        };

		/**
         * Set remotedev device
         */
        self.setRemotedevDevice = function() {
           	for( var i=0; i<cleepService.devices.length; i++ ) {
    	        if( cleepService.devices[i].type==='developer' ) {
                    self.remotedevUuid = cleepService.devices[i].uuid;
                    break;
	            }
    	    }
        };

        /**
         * Set module configuration internally
         */
        self.setConfig = function(config) {
            if( config ) {
                self.config.moduleInDev = config.moduleindev;
                self.selectedModule = config.moduleindev || '';
            }
        };

        /**
         * Select module turns on debug on it and enable module analyze in build helper tab
         */
        self.selectModule = function() {
            developerService.selectApplicationForDevelopment(self.selectedModule)
                .then(function() {
                    // reload configuration
                    return cleepService.reloadModuleConfig('developer');
                })
                .then(function(config) {
                    // save new config
                    self.setConfig(config);

                    // user message
                    if( config.moduleindev ) {
                        toast.success('App "' + self.selectedModule + '" selected for development');
                    } else {
                        toast.success('Development disabled');
                    }
                });
        };

        /**
         * Check selected app
         */
        self.analyzeApplication = function() {
            self.loading = true;
            self.analyzeError = null;

            // check params
            if( !self.config.moduleInDev ) {
                toast.error('Please select an application');
                self.loading = false;
                return;
            }

            // check app
            toast.loading('Analyzing application...');
            developerService.checkApplication(self.config.moduleInDev)
                .then(function(resp) {
                    self.checkData = resp.data;
                    self.checkData.backend.metadata.longdescription = self.sceLongDescription = $sce.trustAsHtml(self.checkData.backend.metadata.longdescription);
                    self.checkData.errorsCount = resp.data.backend.errors.length + resp.data.frontend.errors.length + resp.data.tests.errors.length + resp.data.scripts.errors.length
                    self.checkData.warningsCount = resp.data.backend.warnings.length + resp.data.frontend.warnings.length + resp.data.tests.warnings.length + resp.data.scripts.warnings.length
                    self.checkData.backend.metadata.urls.site = self.__buildHref(self.checkData.backend.metadata.urls.site);
                    self.checkData.backend.metadata.urls.info = self.__buildHref(self.checkData.backend.metadata.urls.info);
                    self.checkData.backend.metadata.urls.help = self.__buildHref(self.checkData.backend.metadata.urls.help);
                    self.checkData.backend.metadata.urls.bugs = self.__buildHref(self.checkData.backend.metadata.urls.bugs);
                    self.checkData.versionOk = !resp.data.changelog.unreleased && resp.data.changelog.version === resp.data.backend.metadata.version;
                    self.checkData.frontend.filesItems = self.__buildFrontendFiles(self.checkData.frontend.files);
                    const { drivers, events, formatters, misc, module } = self.__buildBackendFiles(self.checkData.backend.files);
                    self.checkData.backend.filesDrivers = drivers;
                    self.checkData.backend.filesEvents = events;
                    self.checkData.backend.filesFormatters = formatters;
                    self.checkData.backend.filesMisc = misc;
                    self.checkData.backend.filesModule = module;
                    self.checkData.tests.filesItems = self.__buildTestsFiles(self.checkData.tests.files);

                    self.selectedNav = 'buildmodule';
                }, function(error) {
                    self.analyzeError = error;
                })
                .finally(function() {
                    toast.close();
                    self.loading = false;
                });
        };

        self.__buildTestsFiles = function (files) {
            return files.map(file => ({
                title: file.filename,
            }));
        };

        self.__buildFrontendFiles = function (files) {
            return files.map(file => ({
                title: file.filename,
                subtitle: 'Usage ' + file.usage,
            }));
        };

        self.__buildBackendFiles = function (files) {
            const drivers = files.drivers.map(file => ({
                title: file.path,
            }));
            const events = files.events.map(file => ({
                title: file.path,
            }));
            const formatters = files.formatters.map(file => ({
                title: file.path,
            }));
            const misc = files.misc.map(file => ({
                title: file.path,
            }));
            const module = [{
                title: files.module.path,
            }];

            return {
                drivers,
                events,
                formatters,
                misc,
                module,
            };
        };

        self.__buildHref = function (url) {
            if (!url) {
                return null;
            }
            return '<a href="' + url + '" target="_blank">'+ url +'</a>';
        };

        /**
         * Build application
         */
        self.buildApplication = function() {
            if( !self.checkData ) {
                return;
            }

            self.loading = true;
            toast.loading('Building application...');
            developerService.buildApplication(self.config.moduleInDev, 30)
                .then(function(resp) {
                    // build generation completed, download package now
                    return developerService.downloadApplication();
                }, function(err) {
                    return $q.reject('stop-chain');
                })
                .then(function(resp) {
                    toast.success('Application built successfully');
                }, function(err) {
                    if (err !== 'stop-chain') {
                        console.error('Download failed:', err);
                        toast.error('Download failed');
                    }
                })
                .finally(function() {
                    self.loading = false;
                });
        };

        /**
         * Clear logs
         */
        self.clearLogs = function()
        {
            self.loading = true;

            systemService.clearLogs()
                .then(function() {
                    toast.info('Log file is cleared');
                })
                .finally(function() {
                    self.loading = false;
                });
        };

        self.openLogs = function () {
            const logUrl = $location.protocol() + '://' + $location.host() + '/logs';
            $window.open(logUrl, '_blank');
        };

        /**
         * Create new application skeleton
         */
        self.createApplication = function(value) {
            self.loading = true;

            developerService.createApplication(value)
                .then(function() {
                    self.openDialog();
                })
                .finally(() => {
                    self.loading = false;
                });
        };

        /**
         * Launch unit tests
         */
        self.launchTests = function() {
            self.loading = true;
            toast.info('Running unit tests. Please follow process in output');

            developerService.launchTests(self.config.moduleInDev)
                .then(function(resp) {
                    if (resp.data) {
                        toast.info('Unit tests running...');
                    }
                })
                .finally(() => {
                    self.loading = false;
                });
        };

        /**
         * Get last coverage report
         */
        self.getLastCoverageReport = function() {
            self.loading = true;
            toast.info('Getting app coverage. Please follow process in output');

            developerService.getLastCoverageReport(self.config.moduleInDev)
                .then(function(resp) {
                    if (resp.data) {
                        toast.info('Last report will be displayed in test output in few seconds');
                    }
                })
                .finally(() => {
                    self.loading = false;
                });
        };

        self.generateApiDocumentation = function() {
            self.loading = true;
            toast.info('Generating API documentation. Please follow process in output');

            developerService.generateApiDocumentation(self.config.moduleInDev)
                .then(function(resp) {
                    if (resp.data) {
                        toast.info('Generating API documentation...');
                    }
                })
                .finally(() => {
                    self.loading = false;
                });
        };

        self.downloadApiDocumentation = function() {
            developerService.downloadApiDocumentation(self.config.moduleInDev);
        };

        self.generateDocumentation = function() {
            self.loading = true;
            toast.loading('Checking application documentation...');

            developerService.generateDocumentation(self.config.moduleInDev)
                .then((valid) => {
                    if (!valid) {
                        toast.error('Documentation is invalid. Please fix it');
                    }
                })
                .finally(() => {
                    self.loading = false;
                    toast.close();
                });
        };

        /**
         * Detect breaking changes
         */
        self.detectBreakingChanges = function() {
            self.loading = true;
            toast.loading('Detecting breaking changes...');

            developerService.detectBreakingChanges(self.config.moduleInDev)
                .finally(() => {
                    self.loading = false;
                    toast.close();
                });
        };

        /**
         * Open new app dialog
         */
        self.openDialog = function() {
            return $mdDialog.show({
                controller: function() { return self; },
                controllerAs: 'developerCtl',
                templateUrl: 'new-app.dialog.html',
                parent: angular.element(document.body),
                clickOutsideToClose: false,
                escapeToClose: false,
                fullscreen: true,
            });
        };

        /**
         * Close dialog and restart cleep
         */
        self.restartCleep = function() {
            $mdDialog.cancel();
            systemService.restart();
        };

        $rootScope.$watchCollection(
            () => self.developerService.testsOutput,
            (output) => {
                self.testsOutput = (!output?.length ? '' : output.join('\n'));
            },
        );

        $rootScope.$watchCollection(
            () => self.developerService.docsOutput,
            (output) => {
                self.docsOutput = (!output?.length ? '' : output.join('\n'));
                self.isDocsHtml = false;
            },
        );

        $rootScope.$watchCollection(
            () => self.developerService.docsHtml,
            (output) => {
                self.docsOutput = (!output?.length ? '' : output);
                self.isDocsHtml = true;
            },
        );

        $rootScope.$watchCollection(
            () => self.developerService.breakingChanges,
            (output) => {
                if (!output || !Object.keys(output).length) {
                    self.breakingChanges = undefined;
                    return;
                }

                self.breakingChanges = '';

                if (output.errors?.length === 0) {
                    self.breakingChanges += 'No breaking changes were detected<br>';
                } else if (output.errors?.length > 0) {
                    self.breakingChanges += 'Detected breaking changes:<ul>';
                    for (const error of output.errors) {
                        self.breakingChanges += '<li>' + error + '</li>';
                    }
                    self.breakingChanges += '</ul><br>';
                }

                if (output.warnings?.length === 0) {
                    self.breakingChanges += 'No warnings were detected<br>';
                } else if (output.warnings?.length > 0) {
                    self.breakingChanges += 'Warnings:<ul>';
                    for (const warning of output.warnings) {
                        self.breakingChanges += '<li>' + warning + '</li>';
                    }
                    self.breakingChanges += '</ul><br>';
                }
            },
        );

    }];

    return {
        templateUrl: 'developer.config.html',
        replace: true,
        controller: developerController,
        controllerAs: 'devCtl'
    };
}]);


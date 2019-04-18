/**
 * Developer service
 * Handle developer module requests
 */
var developerService = function($q, $rootScope, rpcService, raspiotService, appToolbarService, $window)
{
    var self = this;
    self.restartButtonId = null;
    self.testsOutput = [];
    self.docsOutput = [];

    /**
     * Start remotedev
     */
    self.startRemotedev = function()
    {
        return rpcService.sendCommand('start_remotedev', 'developer', 15);
    };

    /**
     * Stop remotedev
     */
    self.stopRemotedev = function()
    {
        return rpcService.sendCommand('stop_remotedev', 'developer', 15);
    };

    /**
     * Analyze module
     */
    self.analyzeModule = function(moduleName)
    {
        return rpcService.sendCommand('analyze_module', 'developer', {'module_name':moduleName}, 30);
    };

    /**
     * Generate desc.json file
     */
    self.generateDescJson = function(jsFiles, icon)
    {
        return rpcService.sendCommand('generate_desc_json', 'developer', {'js_files': jsFiles, 'icon':icon});
    };

    /**
     * Build module package
     */
    self.buildPackage = function(moduleName, data)
    {
        return rpcService.sendCommand('build_package', 'developer', {'module_name': moduleName, 'data': data});
    };

    /**
     * Download module package
     */
    self.downloadPackage = function()
    {
        return rpcService.download('download_package', 'developer');
    };

    /**
     * Set module in development
     */
    self.setModuleInDev = function(moduleName) {
        return rpcService.sendCommand('set_module_in_development', 'developer', {'module_name': moduleName}, 10);
    };

    /**
     * Create new applicatin skeleton
     */
    self.createApplication = function(moduleName) {
        return rpcService.sendCommand('create_application', 'developer', {'module_name': moduleName}, 10);
    };

    /**
     * Launch unit tests
     */
    self.launchTests = function(moduleName) {
        self.testsOutput.splice(0, self.testsOutput.length);
        return rpcService.sendCommand('launch_tests', 'developer', {'module_name': moduleName});
    };

    /**
     * Get last coverage report
     */
    self.getLastCoverageReport = function(moduleName) {
        self.testsOutput.splice(0, self.testsOutput.length);
        return rpcService.sendCommand('get_last_coverage_report', 'developer', {'module_name': moduleName});
    };

    /**
     * Generate documentation
     */
    self.generateDocumentation = function(moduleName) {
        self.docsOutput.splice(0, self.testsOutput.length);
        return rpcService.sendCommand('generate_documentation', 'developer', {'module_name': moduleName});
    };

    /**
     * Download html documentation
     */
    self.downloadDocumentation = function(moduleName) {
        return rpcService.sendCommand('download_documentation', 'developer', {'module_name': moduleName});
    };

    /**
     * Restart CleepOS
     */
    self.restartCleepBackend = function()
    {
        raspiotService.restart(0);
    };

    /**
     * Handle restart cleepos toobar button
     */
    self.handleRestartButton = function(config)
    {
        //drop invalid config
        if( config===undefined || config===null )
        {
            return;
        }

        if( config.moduleindev && !self.restartButtonId )
        {
            self.restartButtonId = appToolbarService.addButton('Dev: restart backend', 'restart', self.restartCleepBackend, 'md-accent');
        }
        else if( !config.moduleindev && self.restartButtonId )
        {
            appToolbarService.removeButton(self.restartButtonId);
            self.restartButtonId = null;
        }
    };

    /**
     * Watch for config changes
     */
    $rootScope.$watchCollection(function() {
        return raspiotService.modules['developer'];
    }, function(newConfig, oldConfig) {
        if( newConfig )
        {
            self.handleRestartButton(newConfig.config);
        }
    });

    /**
     * Catch cleep-cli stoped events
     */
    $rootScope.$on('developer.frontend.restart', function(event, uuid, params) {
        $window.location.reload(true);
    });

    /**
     * Catch tests events
     */
    $rootScope.$on('developer.tests.output', function(event, uuid, params) {
        self.testsOutput.push(params.message);
    });

    /**
     * Catch docs events
     */
    $rootScope.$on('developer.docs.output', function(event, uuid, params) {
        self.docsOutput.push(params.message);
    });

};
    
var RaspIot = angular.module('RaspIot');
RaspIot.service('developerService', ['$q', '$rootScope', 'rpcService', 'raspiotService', 'appToolbarService', '$window', developerService]);


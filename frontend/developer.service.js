/**
 * Developer service
 * Handle developer module requests
 */
angular
.module('Cleep')
.service('developerService', ['$q', '$rootScope', 'rpcService', 'cleepService', 'appToolbarService', '$window',
function($q, $rootScope, rpcService, cleepService, appToolbarService, $window) {
    var self = this;
    self.testsOutput = [];
    self.docsOutput = [];

    /**
     * Start remotedev
     */
    self.startRemotedev = function() {
        return rpcService.sendCommand('start_remotedev', 'developer', 15);
    };

    /**
     * Stop remotedev
     */
    self.stopRemotedev = function() {
        return rpcService.sendCommand('stop_remotedev', 'developer', 15);
    };

    /**
     * Check application
     */
    self.checkApplication = function(moduleName) {
        return rpcService.sendCommand('check_application', 'developer', {'module_name':moduleName}, 30);
    };

    /**
     * Build application package
     */
    self.buildApplication = function(moduleName, data) {
        return rpcService.sendCommand('build_application', 'developer', {'module_name': moduleName}, 60);
    };

    /**
     * Download application package
     */
    self.downloadApplication = function() {
        return rpcService.download('download_application', 'developer');
    };

    /**
     * Select application for development
     */
    self.selectApplicationForDevelopment = function(moduleName) {
        return rpcService.sendCommand('select_application_for_development', 'developer', {'module_name': moduleName}, 10);
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
        self.docsOutput.splice(0, self.docsOutput.length);
        return rpcService.sendCommand('generate_documentation', 'developer', {'module_name': moduleName});
    };

    /**
     * Download html documentation
     */
    self.downloadDocumentation = function(moduleName) {
        return rpcService.download('download_documentation', 'developer', {'module_name': moduleName});
    };

    /**
     * Watch for config changes
     */
    /*$rootScope.$watchCollection(function() {
        return cleepService.modules['developer'];
    }, function(newConfig, oldConfig) {
        if( newConfig ) {
        }
    });*/

    /**
     * Catch cleep-cli stoped events
     **/
    $rootScope.$on('developer.frontend.restart', function(event, uuid, params) {
        $window.location.reload(true);
    });

    /**
     * Catch tests events
     */
    $rootScope.$on('developer.tests.output', function(event, uuid, params) {
        self.testsOutput = self.testsOutput.concat(params.messages);
    });

    /**
     * Catch docs events
     */
    $rootScope.$on('developer.docs.output', function(event, uuid, params) {
        self.docsOutput = self.docsOutput.concat(params.messages);
    });
}]);


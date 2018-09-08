/**
 * Developer service
 * Handle developer module requests
 */
var developerService = function($q, $rootScope, rpcService, raspiotService, appToolbarService)
{
    var self = this;
    self.restartButtonId = null;

    /**
     * Restart raspiot
     */
    self.restartRaspiot = function()
    {
        return rpcService.sendCommand('restart_raspiot', 'developer', 10);
    };

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
    self.analyzeModule = function(module)
    {
        return rpcService.sendCommand('analyze_module', 'developer', {'module':module}, 30);
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
    self.buildPackage = function(module, data)
    {
        return rpcService.sendCommand('build_package', 'developer', {'module': module, 'data': data});
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
    self.setModuleInDev = function(module) {
        return rpcService.sendCommand('set_module_in_development', 'developer', {'module': module}, 10);
    };

    /**
     * Restart CleepOS
     */
    self.restartCleepOs = function()
    {
        raspiotService.restart(0);
    };

    /**
     * Handle restart cleepos toobar button
     */
    self.handleRestartButton = function(config)
    {
        if( config.moduleindev && !self.restartButtonId )
        {
            self.restartButtonId = appToolbarService.addButton('Restart CleepOS', 'restart', self.restartCleepOs, 'md-accent');
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
     * Catch remotedev started events
     */
    $rootScope.$on('developer.remotedev.started', function(event, uuid, params) {
        for( var i=0; i<raspiotService.devices.length; i++ )
        {
            if( raspiotService.devices[i].uuid==uuid )
            {
                if( raspiotService.devices[i].running===false )
                {
                    raspiotService.devices[i].running = true;
                    break;
                }
            }
        }
    });

    /**
     * Catch remotedev stoped events
     */
    $rootScope.$on('developer.remotedev.stopped', function(event, uuid, params) {
        for( var i=0; i<raspiotService.devices.length; i++ )
        {
            if( raspiotService.devices[i].uuid==uuid )
            {
                if( raspiotService.devices[i].running===true )
                {
                    raspiotService.devices[i].running = false;
                    break;
                }
            }
        }
    });
};
    
var RaspIot = angular.module('RaspIot');
RaspIot.service('developerService', ['$q', '$rootScope', 'rpcService', 'raspiotService', 'appToolbarService', developerService]);


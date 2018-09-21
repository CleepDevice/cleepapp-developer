/**
 * Dveloper widget directive
 * Display developer dashboard widget
 */
var widgetDeveloperDirective = function() {

    var widgetDeveloperController = ['$scope', 'developerService', 'raspiotService', function($scope, developerService, raspiotService)
    {
        var self = this;
        self.device = $scope.device;

        //restart cleepos
        self.restartCleepOs = function() {
            raspiotService.restart(0)
        };

        //start remotedev
        self.startRemotedev = function() {
            developerService.startRemotedev()
                .then(function(resp) {
                    if( resp.data )
                        self.device.running = true;
                });
        };

        //stop remotedev
        self.stopRemotedev = function() {
            developerService.stopRemotedev()
                .then(function(resp) {
                    if( resp.data )
                        self.device.running = false;
                });
        };
    }];

    return {
        restrict: 'EA',
        templateUrl: 'developer.widget.html',
        replace: true,
        scope: {
            'device': '='
        },
        controller: widgetDeveloperController,
        controllerAs: 'widgetCtl'
    };
};

var RaspIot = angular.module('RaspIot');
RaspIot.directive('widgetDeveloperDirective', [widgetDeveloperDirective]);


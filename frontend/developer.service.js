/**
 * Developer service
 * Handle developer module requests
 */
angular
.module('Cleep')
.service('developerService', ['$q', '$rootScope', 'rpcService', 'cleepService', '$window', '$timeout',
function($q, $rootScope, rpcService, cleepService, $window, $timeout) {
    var self = this;
    self.testsOutput = [];
    self.docsOutput = [];
    self.docsHtml = "";
    self.breakingChanges = {};

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
     * Generate API documentation
     */
    self.generateApiDocumentation = function(moduleName) {
        self.__resetDoc();
        return rpcService.sendCommand('generate_api_documentation', 'developer', {'module_name': moduleName});
    };

    /**
     * Download html API documentation
     */
    self.downloadApiDocumentation = function(moduleName) {
        self.__resetDoc();
        return rpcService.download('download_api_documentation', 'developer', {'module_name': moduleName});
    };

    /**
     * Generate documentation
     */
    self.generateDocumentation = function(moduleName) {
        self.__resetDoc();
        return rpcService.sendCommand('generate_documentation', 'developer', {'module_name': moduleName}, 15)
            .then((resp) => {
                if (!resp.error) {
                    self.docsHtml = self.__checkDocToHtml(resp.data.doc, resp.data.check);
                }

                return resp.data.valid;
            });
    };

    /**
     * Detect breaking changes
     */
    self.detectBreakingChanges = function(moduleName) {
        return rpcService.sendCommand('detect_breaking_changes', 'developer', {'module_name': moduleName}, 30)
            .then((resp) => {
                if (!resp.error) {
                    self.breakingChanges = resp.data;
                }
            });
    };

    /**
     * Reset docs variables
     */
    self.__resetDoc = function() {
        self.docsOutput.splice(0, self.docsOutput.length);
        self.docsHtml = "";
    };

    /**
     * Transform check doc from json to html
     */
    self.__checkDocToHtml = function(doc, check) {
        let html = "<ul>";
        for (const [fnName, data] of Object.entries(doc)) {
            html += "<li class=\"doc-function\"><span>Command " + fnName + "</span><ul>";

            // errors
            const errors =  check[fnName]?.errors || [];
            if (errors.length > 0) {
                html += self.__docGenerateHtmlErrors(errors);
            }

            // warnings
            const warns =  check[fnName]?.warnings || [];
            if (warns.length > 0) {
                html += self.__docGenerateHtmlErrors(warns);
            }

            // args
            if (data.args?.length > 0) {
                html += "<li><span>Args</span><ul>";
            }
            for (const arg of data.args) {
                const argName = arg.name;
                html += "<li><span>" + argName + "</span><ul><li>Type: " + self.__specialsToHtml(arg.type) + "</li>";
                if (arg.optional) {
                    html += "<li>Optional: true</li>";
                }
                if (arg.default !== null) {
                    html += "<li>default: " + arg.default + "</li>";
                }
                html += "<li>Description: " + arg.description + "</li>";

                html += self.__docGenerateHtmlFormats(arg.formats);
                html += "</ul></li>";
            }
            if (data.args?.length > 0) {
                html += "</ul></li>";
            }

            // returns
            if (data.returns?.length > 0) {
                html += "<li><span>Returns</span><ul>";
            }
            for (const ret of data.returns) {
                html += "<li><span>" + self.__specialsToHtml(ret.type) + "</span>";
                html += "<ul>";
                html += "<li>Description: " + ret.description + "</li>";

                html += self.__docGenerateHtmlFormats(ret.formats);
                html += "</ul></li>";
            }
            if (data.returns?.length > 0) {
                html += "</ul></li>";
            }

            // raises
            if (data.raises?.length > 0) {
                html += "<li><span>Raises</span><ul>";
            }
            for (const raise of data.raises) {
                html += "<li><span>" + self.__specialsToHtml(raise.type) + "</span><ul><li>Description: " + raise.description + "</li>";
                html += "</ul></li>";
            }
            if (data.raises?.length > 0) {
                html += "</ul></li>";
            }
            html += "</ul></li>";
        }
        html += "</ul>";

        return html;
    }

    self.__docGenerateHtmlFormats = function(formats) {
        let html = "";
        if (formats?.length) {
            html += "<li><span>Formats</span>:<ul>";
        }
        for (const format of formats) {
            html += "<li>" + format + "</li>";
        }
        if (formats?.length) {
            html += "</ul></li>";
        }

        return html;
    }

    self.__docGenerateHtmlErrors = function(errors) {
        let html = "";
        if (errors.length > 0) {
            html += "<li><span>Errors:</span><ul class=\"doc-errors\">"
        }
        for (const error of errors) {
            html += "<li>" + error + "</li>";
        }
        if (errors.length > 0) {
            html += "</ul></li>";
        }
        return html;
    }

    self.__docGenerateHtmlWarns = function(warns) {
        let html = "";
        if (warns.length > 0) {
            html += "<li><span>Warnings:</span><ul class=\"doc-warns\">"
        }
        for (const warn of warns) {
            html += "<li>" + warn + "</li>";
        }
        if (warns.length > 0) {
            html += "</ul></li>";
        }
        return html;
    }

    /**
     * Encode specials chars to HTML
     */
    self.__specialsToHtml = function (raw) {
        return raw.replace(/[\u00A0-\u9999<>\&]/g, function(i) {
            return '&#'+i.charCodeAt(0)+';';
        });
    }

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
        $timeout(() => { $window.location.reload(true); }, 1000);
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


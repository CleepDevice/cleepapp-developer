/*global angular*/

/**
 * Components showcase page — interactive catalog for config / UI / widget components.
 */
angular
.module('Cleep')
.directive('componentsPageDirective', [
function() {

    var componentsController = ['$scope', '$interval', 'toastService',
    function($scope, $interval, toast) {
        var self = this;
        self.meta = { source: 'components-showcase', value: 42 };
        self.collapseClosed = false;
        self.collapseOpened = true;
        self.collapseText = 'advanced-value';
        self.collapseSwitch = false;
        self.textContent = 'cleep-dev';
        self.htmlContent = 'See the <a href="https://github.com/CleepDevice/cleepapp-developer/wiki" target="_blank">developer wiki</a>.';
        self.markdownContent = 'Use **config-comment** with `cl-mode="markdown"` for rich help text.';
        self.inputNumber = 8080;
        self.inputText = 'cleep-dev';
        self.inputPassword = 'secret';
        self.inputSlider = 40;
        self.inputCheckbox = true;
        self.inputSwitch = false;
        self.selectOptions = [
            { label: 'HDMI', value: 'hdmi' },
            { label: 'Headphones', value: 'headphones', disabled: true },
            { label: 'Bluetooth', value: 'bluetooth' },
            { label: 'USB DAC', value: 'usb' },
        ];
        self.inputSelect = 'hdmi';
        self.inputSelects = ['hdmi', 'bluetooth'];
        self.inputTime = new Date();
        self.inputDate = new Date();
        self.progress = 0;
        self.chips = ['audio', 'network', 'update'];
        self.emptyList = [];
        self.viewerText = 'modtests: ok\ncoverage: 72%\nready to package';
        self.progressTimer = null;

        function actionClick(label) {
            return function() {
                toast.info(label + ' clicked');
                console.log('components showcase action', label);
            };
        }

        function listClick(item) {
            toast.info('List action on ' + (item && item.title ? item.title : 'item'));
            console.log('list click', item);
        }

        self.twoButtons = [
            { color: 'md-primary', icon: 'open-in-new', label: 'Open', tooltip: 'Open logs', click: actionClick('Open') },
            { color: 'md-accent', icon: 'delete', label: 'Clear', tooltip: 'Clear logs', disabled: true },
        ];
        self.fourButtons = [
            { color: 'md-primary', icon: 'play', label: 'Start', tooltip: 'Start', click: actionClick('Start'), meta: self.meta },
            { color: 'md-primary', icon: 'stop', label: 'Stop', tooltip: 'Stop', disabled: true },
            { color: 'md-accent', icon: 'restart', label: 'Restart', tooltip: 'Restart', click: actionClick('Restart') },
            { color: 'md-warn', icon: 'delete', label: 'Reset', tooltip: 'Reset', click: actionClick('Reset') },
        ];

        self.listItems = [
            {
                title: 'Living room',
                subtitle: 'light · online',
                icon: 'lightbulb-on',
                iconStyle: 'md-primary',
                meta: { id: 'living-room' },
                clicks: [
                    { tooltip: 'Delete', icon: 'delete', style: 'md-accent', click: listClick },
                    { tooltip: 'Edit', icon: 'pencil', click: listClick, meta: { action: 'edit' } },
                ],
            },
            {
                title: 'Kitchen',
                subtitle: 'sensor · offline',
                icon: 'thermometer',
                iconStyle: 'md-accent',
                meta: { id: 'kitchen' },
                clicks: [
                    { tooltip: 'Delete', icon: 'delete', style: 'md-accent', click: listClick },
                ],
            },
        ];

        self.widgetTitle = 'Living room light';
        self.widgetSubtitle = 'demo device';
        self.widgetIcon = 'lightbulb-on';
        self.widgetDevice = {
            on: true,
            brightness: 75,
            name: 'Living room light',
        };
        self.widgetFooter = [
            {
                type: 'button',
                icon: 'brightness-6',
                label: 'Dim',
                tooltip: 'Lower brightness',
                style: 'md-primary',
                click: function() {
                    self.widgetDevice.brightness = Math.max(0, self.widgetDevice.brightness - 10);
                    toast.info('Brightness ' + self.widgetDevice.brightness + '%');
                },
            },
            {
                type: 'text',
                icon: 'information-outline',
                label: 'demo widget',
                tooltip: 'Showcase footer',
            },
        ];

        self.openDocs = {};
        self.docs = {
            'cl-icon': {
                description: 'Material Design Icons helper. Prefixes the name with mdi- (or brand-).',
                bindings: 'cl-icon, cl-tooltip, cl-class',
                example:
'<cl-icon cl-icon="home" cl-tooltip="Home" cl-class="icon-md"></cl-icon>',
            },
            'config-button': {
                description: 'Single action row with title/subtitle and one button on the right.',
                bindings: 'cl-title, cl-subtitle, cl-icon, cl-btn-label, cl-btn-icon, cl-btn-style, cl-btn-tooltip, cl-click, cl-disabled, cl-meta',
                example:
'<config-button\n' +
'    cl-title="Restart service"\n' +
'    cl-subtitle="Apply changes"\n' +
'    cl-icon="restart"\n' +
'    cl-btn-label="Restart"\n' +
'    cl-btn-icon="play"\n' +
'    cl-click="$ctrl.restart()"\n' +
'></config-button>',
            },
            'config-buttons': {
                description: 'Row with multiple actions. Up to cl-limit (default 2) are shown inline; more go into a menu.',
                bindings: 'cl-title, cl-subtitle, cl-icon, cl-buttons (array), cl-limit',
                example:
'$ctrl.buttons = [\n' +
'  { label: "Open", icon: "open-in-new", click: $ctrl.open, color: "md-primary" },\n' +
'  { label: "Clear", icon: "delete", disabled: true },\n' +
'];\n\n' +
'<config-buttons\n' +
'    cl-title="Log file"\n' +
'    cl-icon="text-box-outline"\n' +
'    cl-buttons="$ctrl.buttons"\n' +
'></config-buttons>',
            },
            'config-checkbox': {
                description: 'Checkbox row. cl-click receives selected/unselected values when provided.',
                bindings: 'cl-model (=), cl-caption, cl-selected-value, cl-unselected-value, cl-title, cl-icon, cl-click, cl-disabled, cl-meta',
                example:
'<config-checkbox\n' +
'    cl-title="Enable debug"\n' +
'    cl-caption="Enabled"\n' +
'    cl-model="$ctrl.debug"\n' +
'    cl-click="$ctrl.onToggle(value, meta)"\n' +
'></config-checkbox>',
            },
            'config-chips': {
                description: 'Chip list bound to a string array. Editable when cl-readonly is false.',
                bindings: 'cl-model (= array), cl-readonly, cl-removable, cl-placeholder, cl-title, cl-icon, cl-click, cl-btn-icon',
                example:
'<config-chips\n' +
'    cl-title="Tags"\n' +
'    cl-model="$ctrl.tags"\n' +
'    cl-removable="true"\n' +
'    cl-readonly="false"\n' +
'    cl-btn-icon="content-save"\n' +
'    cl-click="$ctrl.save(value, meta)"\n' +
'></config-chips>',
            },
            'config-collapse': {
                description: 'Collapsible panel to group optional or advanced settings. Content is projected with transclusion.',
                bindings: 'cl-title, cl-subtitle, cl-icon, cl-icon-style, cl-opened (=?), cl-disabled, cl-id',
                example:
'<config-collapse\n' +
'    cl-title="Advanced options"\n' +
'    cl-subtitle="Optional settings"\n' +
'    cl-icon="cog"\n' +
'    cl-opened="$ctrl.open"\n' +
'>\n' +
'    <config-text cl-title="Extra" cl-model="$ctrl.value"></config-text>\n' +
'</config-collapse>',
            },
            'config-comment': {
                description: 'Read-only value next to a title. Supports plain text, HTML or markdown via cl-mode.',
                bindings: 'cl-title, cl-subtitle, cl-icon, cl-comment (<), cl-mode (text|html|markdown)',
                example:
'<config-comment\n' +
'    cl-title="Hostname"\n' +
'    cl-icon="server"\n' +
'    cl-comment="$ctrl.hostname"\n' +
'></config-comment>\n\n' +
'<config-comment\n' +
'    cl-title="Help"\n' +
'    cl-comment="$ctrl.htmlHelp"\n' +
'    cl-mode="html"\n' +
'></config-comment>',
            },
            'config-date': {
                description: 'Date picker bound to a Date object.',
                bindings: 'cl-model (= Date), cl-min, cl-max, cl-title, cl-icon, cl-click, cl-disabled, cl-meta',
                example:
'<config-date\n' +
'    cl-title="Install date"\n' +
'    cl-model="$ctrl.installDate"\n' +
'    cl-click="$ctrl.save(value, meta)"\n' +
'></config-date>',
            },
            'config-file': {
                description: 'File picker row (uses cl-app-upload). cl-click receives the selected file.',
                bindings: 'cl-title, cl-subtitle, cl-icon, cl-btn-label, cl-btn-icon, cl-click, cl-disabled, cl-meta',
                example:
'<config-file\n' +
'    cl-title="Import configuration"\n' +
'    cl-btn-label="Choose file"\n' +
'    cl-btn-icon="folder-open"\n' +
'    cl-click="$ctrl.onFile(file)"\n' +
'></config-file>',
            },
            'config-list': {
                description: 'List of items with optional selection and per-item action buttons.',
                bindings: 'cl-items, cl-selectable, cl-on-select, cl-empty, cl-empty-icon',
                example:
'$ctrl.items = [{\n' +
'  title: "Living room",\n' +
'  subtitle: "online",\n' +
'  icon: "lightbulb-on",\n' +
'  clicks: [{ icon: "delete", tooltip: "Delete", click: $ctrl.remove }],\n' +
'}];\n\n' +
'<config-list\n' +
'    cl-items="$ctrl.items"\n' +
'    cl-selectable="true"\n' +
'    cl-on-select="$ctrl.onSelect(current, index, selections)"\n' +
'></config-list>',
            },
            'config-note': {
                description: 'Highlighted note block. cl-type: none | note | info | success | warning | error.',
                bindings: 'cl-note (@), cl-type, cl-icon, cl-icon-style, cl-img-src, cl-img-width',
                example:
'<config-note\n' +
'    cl-type="info"\n' +
'    cl-icon="information"\n' +
'    cl-note="Remember to restart after changes."\n' +
'></config-note>',
            },
            'config-number': {
                description: 'Numeric input with optional min/max and save button (cl-click).',
                bindings: 'cl-model (=), cl-min, cl-max, cl-required, cl-title, cl-subtitle, cl-icon, cl-btn-icon, cl-btn-tooltip, cl-click, cl-disabled, cl-meta',
                example:
'<config-number\n' +
'    cl-title="Port"\n' +
'    cl-model="$ctrl.port"\n' +
'    cl-min="1" cl-max="65535"\n' +
'    cl-btn-icon="content-save"\n' +
'    cl-click="$ctrl.save(value, meta)"\n' +
'></config-number>',
            },
            'config-progress': {
                description: 'Progress row. Use cl-infinite for indeterminate mode. Cancel via cl-cancel.',
                bindings: 'cl-model (< number), cl-infinite, cl-title, cl-icon, cl-cancel, cl-style, cl-btn-icon, cl-meta',
                example:
'<config-progress\n' +
'    cl-title="Downloading"\n' +
'    cl-model="$ctrl.progress"\n' +
'    cl-cancel="$ctrl.cancel(value, meta)"\n' +
'></config-progress>\n\n' +
'<config-progress\n' +
'    cl-title="Working"\n' +
'    cl-model="$ctrl.progress"\n' +
'    cl-infinite="true"\n' +
'></config-progress>',
            },
            'config-section': {
                description: 'Section header to separate groups of settings. Optional action button (label, icon, click) aligned to the right.',
                bindings: 'cl-title, cl-icon, cl-btn-label, cl-btn-icon, cl-click',
                example:
'<config-section cl-title="Devices" cl-icon="devices"></config-section>\n\n' +
'<config-section\n' +
'    cl-title="Devices"\n' +
'    cl-icon="devices"\n' +
'    cl-btn-label="Add"\n' +
'    cl-btn-icon="plus"\n' +
'    cl-click="$ctrl.addDevice()"\n' +
'></config-section>',
            },
            'config-select': {
                description: 'Single or multi select. Pass an array to cl-model for multiple choices. Options: {label, value, disabled?}.',
                bindings: 'cl-model (=), cl-options, cl-title, cl-icon, cl-click, cl-change, cl-empty, cl-no-select-all, cl-disabled, cl-meta',
                example:
'$ctrl.options = [\n' +
'  { label: "HDMI", value: "hdmi" },\n' +
'  { label: "USB", value: "usb" },\n' +
'];\n\n' +
'<config-select\n' +
'    cl-title="Output"\n' +
'    cl-options="$ctrl.options"\n' +
'    cl-model="$ctrl.output"\n' +
'    cl-change="$ctrl.onChange(value, $event)"\n' +
'></config-select>',
            },
            'config-slider': {
                description: 'Slider input with min/max/step and optional save button.',
                bindings: 'cl-model (=), cl-min, cl-max, cl-step, cl-title, cl-icon, cl-btn-icon, cl-click, cl-on-change, cl-disabled',
                example:
'<config-slider\n' +
'    cl-title="Volume"\n' +
'    cl-model="$ctrl.volume"\n' +
'    cl-min="0" cl-max="100" cl-step="5"\n' +
'    cl-btn-icon="content-save"\n' +
'    cl-click="$ctrl.save(value, meta)"\n' +
'></config-slider>',
            },
            'config-switch': {
                description: 'Switch row. Optional cl-on-value / cl-off-value customize the value passed to cl-click.',
                bindings: 'cl-model (=), cl-caption, cl-on-value, cl-off-value, cl-title, cl-icon, cl-click, cl-disabled, cl-meta',
                example:
'<config-switch\n' +
'    cl-title="Night mode"\n' +
'    cl-model="$ctrl.nightMode"\n' +
'    cl-on-value="ON" cl-off-value="OFF"\n' +
'    cl-click="$ctrl.onToggle(value, meta)"\n' +
'></config-switch>',
            },
            'config-text': {
                description: 'Text or password input with optional save button.',
                bindings: 'cl-model (=), cl-password, cl-min, cl-max, cl-required, cl-placeholder, cl-title, cl-icon, cl-btn-icon, cl-click, cl-disabled',
                example:
'<config-text\n' +
'    cl-title="Hostname"\n' +
'    cl-model="$ctrl.hostname"\n' +
'    cl-btn-icon="content-save"\n' +
'    cl-click="$ctrl.save(value, meta)"\n' +
'></config-text>\n\n' +
'<config-text\n' +
'    cl-title="Token"\n' +
'    cl-model="$ctrl.token"\n' +
'    cl-password="true"\n' +
'></config-text>',
            },
            'config-text-viewer': {
                description: 'Full-height text (or HTML) viewer with optional toolbar buttons.',
                bindings: 'cl-title, cl-text, cl-is-html, cl-empty, cl-style, cl-buttons',
                example:
'<config-text-viewer\n' +
'    cl-title="Command output"\n' +
'    cl-text="{{ $ctrl.output }}"\n' +
'></config-text-viewer>',
            },
            'config-time': {
                description: 'Time picker bound to a Date object.',
                bindings: 'cl-model (= Date), cl-show-seconds, cl-show-milliseconds, cl-title, cl-icon, cl-click, cl-disabled, cl-meta',
                example:
'<config-time\n' +
'    cl-title="Alarm time"\n' +
'    cl-model="$ctrl.alarm"\n' +
'    cl-click="$ctrl.save(value, meta)"\n' +
'></config-time>',
            },
            'widget-basic': {
                description: 'Dashboard widget shell with title, icon, device-driven background, footer actions and transcluded content.',
                bindings: 'cl-device, cl-title, cl-subtitle, cl-icon, cl-footer, cl-image + <widget-content> / <widget-footer>',
                example:
'<widget-basic\n' +
'    cl-title="$ctrl.title"\n' +
'    cl-subtitle="$ctrl.subtitle"\n' +
'    cl-icon="$ctrl.icon"\n' +
'    cl-device="$ctrl.device"\n' +
'    cl-footer="$ctrl.footer"\n' +
'>\n' +
'    <widget-content layout="column" layout-align="center center">\n' +
'        <div>{{ $ctrl.device.on ? "ON" : "OFF" }}</div>\n' +
'    </widget-content>\n' +
'</widget-basic>',
            },

        };

        self.toggleDoc = function(id) {
            self.openDocs[id] = !self.openDocs[id];
        };

        self.isDocOpen = function(id) {
            return !!self.openDocs[id];
        };

        self.docBtnLabel = function(id) {
            return self.isDocOpen(id) ? 'Hide code' : 'Show code';
        };

        self.docBtnIcon = function(id) {
            return self.isDocOpen(id) ? 'eye-off-outline' : 'code-tags';
        };

        self.$onInit = function() {
            if ($scope.pageCtl && $scope.pageCtl.setToolbar) {
                $scope.pageCtl.setToolbar('Components showcase');
            }
            self.progressTimer = $interval(self.updateProgress, 1000);
        };

        $scope.$on('$destroy', function() {
            if (self.progressTimer) {
                $interval.cancel(self.progressTimer);
                self.progressTimer = null;
            }
        });

        self.updateProgress = function() {
            self.progress += 10;
            if (self.progress >= 100) {
                self.progress = 0;
            }
        };

        self.onAction = function(label) {
            toast.info((label || 'Action') + ' clicked');
            console.log('components showcase action', label);
        };

        self.onClick = function(value, meta) {
            const summary = typeof value === 'undefined' || value === null
                ? 'Action triggered'
                : 'Value: ' + (angular.isObject(value) ? angular.toJson(value) : value);
            toast.info(summary);
            console.log('components showcase click', { value: value, meta: meta });
        };

        self.onSelect = function(current, index, selections, event) {
            toast.info('Selection changed at index ' + index);
            console.log('components showcase select', { current: current, index: index, selections: selections, event: event });
        };

        self.onSelectChange = function(valueOrValues, event) {
            toast.info('Select changed');
            console.log('components showcase select change', { valueOrValues: valueOrValues, event: event });
        };

        self.onFile = function(file) {
            const name = file && (file.name || file.filename) ? (file.name || file.filename) : 'file';
            toast.info('Selected ' + name);
            console.log('components showcase file', file);
        };

        self.onWidgetToggle = function(value) {
            toast.info(value ? 'Device ON' : 'Device OFF');
        };
    }];

    return {
        templateUrl: 'components.html',
        replace: true,
        scope: true,
        controller: componentsController,
        controllerAs: '$ctrl',
    };
}])
.directive('componentsDocPanel', [function() {
    return {
        restrict: 'E',
        scope: {
            open: '<',
            doc: '<',
        },
        template:
            '<md-card ng-if="open && doc" class="components-doc-card">' +
                '<md-card-content>' +
                    '<div class="md-subhead components-doc-title">Usage</div>' +
                    '<div class="md-body-1 components-doc-desc">{{ doc.description }}</div>' +
                    '<div class="md-caption components-doc-bindings" ng-if="doc.bindings">' +
                        '<strong>Bindings:</strong> {{ doc.bindings }}' +
                    '</div>' +
                    '<pre class="components-doc-code">{{ doc.example }}</pre>' +
                '</md-card-content>' +
            '</md-card>',
    };
}]);

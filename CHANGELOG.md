# Changelog

## [UNRELEASED]
### Added
- Check application documentation before generating release archive
- Add breaking changes detection feature

### Updated
- Change documentation tab using new doc core command
- Bump cleepcli to v1.32.0
- Improve UI

### Fixed
- When last coverage report button is clicked all buttons remain disabled
- Tests execution return_code is displayed instead of number in result output

## [3.1.0] - 2023-03-14
### Fixed
- Handle command failure (return code different from 0)
- Reset analyze error flag when running new analysis
- Improve code quality (black+lint)

### Changed
- Improve app creation: temporarily disable cleep-cli watch and add infos dialog
- Add some log messages

## [3.0.0] - 2021-10-16
### Added
- Full code coverage
- Review layout

### Fixed
- Small issues discovered during unit tests writing

### Removed
- Functionnalities deported to cleep-cli
- Logs display that already exists on core system app

## [2.2.0] - 2019-09-30
## Changed
- Update after core changes
- Fix some issues

## [2.1.0] - 2019-05-03
## Changed
- Update cleep-cli version
- Handle module tests
- Handle module documentationSome improvements: add notes, sort files list, update desc.json file generation

## [2.0.0] - 2019-04-22
## Changed
- Replace remotedev by cleep-cli usage. Simpler to use and to maintain
- Module documentation generation
- Module tests execution
- Some UI enhancements

## [1.0.2] - 2019-02-16
## Fixed
- Deep scan error during frontend files analysis
- Bug in list of selectable modules

## Changed
- Reset previous analysis content when restarting raspiot

## [1.0.1] - 2018-11-22
## Changed
- Fix install issues
- Fix small frontend issues

## [1.0.0] - 2019-10-07
## Changed
- First official release


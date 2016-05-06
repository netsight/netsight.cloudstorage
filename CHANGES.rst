Changelog
=========

1.8.1 (2016-05-06)
------------------

- Remove dependency on plone.namedfile
  [mattss]


1.8 (2016-02-09)
----------------

- Provide an example of how to install and configure a redis server
  with buildout [erral]

- Add a control panel option to disable transcoding [erral]

- Better support of dexterity content-types using plone.namedfile.
  Now dexterity types' blobs are uploaded automatically to cloud
  storage [erral]

- Allow generating differing expiry URLs [benc]

- Remove files from cloud when removed from Plone [mattss]

1.7.1 (2014-12-11)
------------------

- Fixed issue with a log line [benc]


1.7 (2014-12-09)
----------------

- Handling of content with multiple fields where at least one is below file
  size threshold [benc]


1.6.9 (2014-12-09)
------------------

- Added more verbose logging throughout [benc]

1.6.8 (2014-12-09)
------------------

- Added more verbose error logging to callback task
  [benc]
- Added more logging to callback view
  [benc]
- Updated requests required version
  [benc]


1.6.7 (2014-12-08)
------------------

- Added more logging to upload_callback to aid debugging
  [benc]


1.6.6 (2014-11-27)
------------------

- Removed bucket creation in transcoding - no longer needed as not creating pipeline
  [benc]
- Fixed email notifications configuration
  [benc]


1.6.5 (2014-11-27)
------------------

- Removed pipeline creation
  [benc]
- Made pipeline name optional in control panel
  [benc]


1.6.1 (2014-11-21)
------------------

- Added workaround for "connection reset by peer"
  [benc]


1.6 (2014-11-17)
----------------

- Added abaility to disable email notifications
  [benc]


1.5 (2014-11-06)
----------------

- Added transcoding for video files
  [benc]
- Added customisable pipeline name
  [benc]
- Added fleshed out README
  [mattss]
- Added travis config
  [mattss]


1.4 (2014-10-23)
----------------

- AWS transcoding support!
  [benc]
- Improved support for virtual hosts
  [benc, mattss]


1.3 (2014-10-22)
----------------

- Half-baked release
  [names removed to protect the innocent]


1.2 (2014-09-26)
----------------

- General help text updates
  [mattss]
- Clear cloud storage setting when re-queued
  [mattss]


1.1 (2014-09-25)
----------------

- Switch to chunked uploads
  [benc]
- Fix bug with download patch
  [mattss]
- Add correct filename and mimetype to url generator
  [mattss]
- Add manual upload trigger view
  [benc]


1.0 (2014-09-23)
----------------

- Initial release
  [benc]

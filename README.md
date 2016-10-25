# oxide-plugin-updater

## Introduction:

This script updates every Oxide plugin (www.oxidemod.org) of a given folder to its latest version. 

## Requirements:

* Python 2.7.
* Python module requests.

## Installation:

1. Get python 2.7.X from https://www.python.org/downloads/
2. Install requests module with python PIP (pip install requests)

## How to run:

```python plugin_updater -pluginDir "YOUR/OXIDE/PLUGIN/DIR" -login "OXIDEORG-LOGIN" -password "OXIDEORG-PASSWORD"```

## Limitations:
* Only works with plugins that define ResourceId.
* For now only supports C#, lua and python plugins.

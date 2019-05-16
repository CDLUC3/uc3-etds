#/usr/bin/python
import yaml
campus='/home/uc3/etds/config/campus.yml'
app='/home/uc3/etds/config/app_config.yml'
with open(campus, 'r') as cmp_cfg:
    campus_configs = yaml.load(cmp_cfg)

with open(app, 'r') as app_cfg:
    app_configs = yaml.load(app_cfg)
 


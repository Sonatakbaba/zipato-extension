# -*- coding: utf-8 -*-
"""
.. moduleauthor:: John Brännström <john.brannstrom@gmail.com>

Settings
********

This module contains settings.

"""

import yaml
import os
import re
from flask import render_template


class Settings:
    """Settings container."""

    __CONFIG_FILE = 'zipatoserver.conf'
    """(*str*) Config file name."""

    __PATH_WITH_SLASH_PARAMETERS = [
        'WEB_API_PATH', 'WEB_GUI_PATH', 'WAKEONLAN_PATH', 'PING_PATH',
        'SSH_PATH']
    """(*list*) Parameters in this list with always end with a slash."""

    __PATH_WITHOUT_SLASH_PARAMETERS = [
        'MESSAGE_LOG', 'ERROR_LOG', 'SSH_KEY_FILE']
    """(*list*) Parameters in this list will never end with a slash."""

    PROGRAM_PATH = None
    """(*str*) Path of the program."""

    @staticmethod
    def _get_config_file(settings_path, program_path):
        """
        Get full path and name of the YAML config file.
        
        :param str settings_path: Path to the YAML config file.
        :param str program_path: Path to the program.
        :rtype: str
        :returns: Full path and name of the config file.
        
        """
        if settings_path is not None:
            config_file = Settings._format_path(settings_path)
            config_file += Settings.__CONFIG_FILE
        else:
            config_file = program_path + Settings.__CONFIG_FILE
        return config_file

    @staticmethod
    def load_settings_from_yaml(settings_path=None):
        """
        Set system constants from YAML file.

        :param str settings_path: If supplied this will determine the location
                                  of the YAML file. If not, YAML file will be
                                  read from the current directory.

        """
        Settings.PROGRAM_PATH = program_path = (
            os.path.dirname(os.path.abspath(__file__)) + '/')
        config_file = Settings._get_config_file(settings_path, program_path)
        with open(config_file, 'r') as f:
            constants = yaml.load(f)
        for constant, value in constants.items():
            setattr(Settings, constant, Settings._format_value(constant, value))

    @staticmethod
    def _format_path(path, slash=True):
        """
        Format a path string.

        :param str path: Path to format.
        :param bool slash: If the path string should end with a slash
        :rtype: str
        :return: A formatted path string.

        """
        if len(path) == 0:
            return path
        elif slash and path[-1] != '/':
            return path + '/'
        elif not slash and path[-1] == '/':
            return path[:-1]
        return path

    @staticmethod
    def _format_value(param, value):
        """
        Format parameter value.

        :param str param: Name of the parameter to format.
        :param str param: Value to format.
        :rtype: str or bool
        :return: A parameter with the correct type.

        """
        if param in Settings.__PATH_WITH_SLASH_PARAMETERS:
            return Settings._format_path(value, True)
        elif param in Settings.__PATH_WITHOUT_SLASH_PARAMETERS:
            return Settings._format_path(value, False)
        elif str(value).lower() == 'yes' or str(value).lower() == 'true':
            return True
        elif str(value).lower() == 'no' or str(value).lower() == 'false':
            return False
        try:
            return int(value)
        except (TypeError, ValueError):
            return value

    @staticmethod
    def render_settings_html(settings_path=None):
        """
        Render web GUI for handling settings.

        :param str settings_path: If supplied this will determine the location
                                  of the YAML file. If not, YAML file will be
                                  read from the current directory.

        """
        program_path = (
            os.path.dirname(os.path.abspath(__file__)) + '/')
        config_file = Settings._get_config_file(settings_path, program_path)
        # Load constants from disk
        with open(config_file, 'r') as f:
            constants = yaml.load(f)
        for constant, value in constants.items():
            constants[constant] = Settings._format_value(constant, value)
        # Load comments from disk
        comments = {}
        file = open(config_file, encoding='utf-8')
        lines = file.readlines()
        for i in range(len(lines)-1, -1, -1):
            # Test/set more comments
            if re.match('\A#.*', lines[i]):
                comments[constant] = (
                    lines[i][1:].strip() + ' ' + comments[constant])
            for key in constants.keys():
                # Test/set new constant
                regex = "\A{}:.*".format(key)
                if re.match(regex, lines[i]):
                    constant = key
                    comments[constant] = ''
        return render_template('settings.html',
                               constants=constants,
                               comments=comments,
                               save_settings_path=(
                                   Settings.WEB_API_PATH + 'save_settings'),
                               remove_param_path=(
                                   Settings.WEB_API_PATH + 'remove_param'),
                               add_param_path=(
                                   Settings.WEB_API_PATH + 'add_param')
                               )

    @staticmethod
    def remove_value_from_file(param, value):
        """
        Remove a value from a parameter in the settings file.

        :param str param: Parameter to remove value from.
        :param str value: Value (dict) to remove from parameter.

        """
        with open(config_file, 'r') as f:
            settings_json = yaml.load(f)
        # TODO remove parameter from dict here and then write to disk as shown below        
        self.write_settings_to_file(settings_json, settings_path='/etc')

    @staticmethod
    def write_settings_to_file(settings_json, settings_path=None):
        """
        Write settings to file.

        :param dict settings_json: Settings that should be written to file.
        :param str settings_path: If supplied this will determine the location
                                  of the YAML file. If not, YAML file will be
                                  written/read to/from the current directory.

        ..note:

            Comments are only supported on top level parameters.

        """
        program_path = (ya
            os.path.dirname(os.path.abspath(__file__)) + '/')
        config_file = Settings._get_config_file(settings_path, program_path)
        file_obj = open(config_file, 'r', encoding="utf-8")
        # Read YAML file comments from disk.
        lines = file_obj.readlines()
        file_obj.close()
        # Get all comments
        comment = []
        param_comments = {}
        for i in range(len(lines)):
            if len(lines[i]) > 0 and lines[i][0] == '#':
                comment.append(lines[i].strip())
                if lines[i+1][0] != '#':
                    param = re.match('(.+?):.*', lines[i+1]).group(1)
                    param_comments[param] = comment
                    comment = []
        # Set correct type of parameters
        for param, value in settings_json.items():
            settings_json[param] = Settings._format_value(param, value)
        # Create YAML with comments
        settings_yaml = yaml.dump(settings_json,
                                  default_flow_style=False,
                                  indent=4)
        settings_list = settings_yaml.split('\n')
        i = 0
        while i < len(settings_list):
            top_level_param = re.match('\A(\S+):.*\Z', settings_list[i])
            # Top level parameter found
            if top_level_param is not None:
                param = top_level_param.group(1)
                settings_list.insert(i, '')  # Add newline
                i += 1
                for test_param, comments in param_comments.items():
                    if param == test_param:
                        # Insert parameter comment
                        for comment in comments:
                            settings_list.insert(i, comment)
                            i += 1
                        del param_comments[param]
                        break
            i += 1
        settings_yaml = '\n'.join(settings_list)[1:]
        #  Write YAML to file
        with open(config_file+'~', 'w') as file_obj:
            file_obj.writelines(settings_yaml)
        os.rename(config_file+'~', config_file)

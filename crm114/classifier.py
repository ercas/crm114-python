#!/usr/bin/env python2

import os
import subprocess

CRM_BINARY = 'crm'

CLASSIFICATION_TYPE = '<osb unique microgroom>'
CLASSIFICATION_EXT = '.css'

LEARN_CMD = " '-{ learn %s ( %s ) }'"
CLASSIFY_CMD = " '-{ isolate (:stats:);" \
               " classify %s ( %s ) (:stats:);" \
               " match [:stats:] (:: :best: :prob:)" \
               " /Best match to file .. \(%s\/([[:graph:]]+)\\%s\)" \
               " prob: ([0-9.]+)/;" \
               " output /:*:best:\\t:*:prob:/ }'"


class Classifier(object):
    def __init__(self, path, categories=None):
        """ Wrapper class for the CRM-114 Discriminator. """
        self.categories = categories if categories else []
        self.path = path
        self.create_files()

    # learn the classifier what category some new text is in
    def learn(self, category, text):
        """ Feed the classifier some new text and a known classification for
        it, in order to improve subsequent categorizations. """

        command = CRM_BINARY + (LEARN_CMD % (CLASSIFICATION_TYPE,
                                             os.path.join(self.path, category +
                                                          CLASSIFICATION_EXT)))

        proc = subprocess.Popen(
            command,
            shell = True,
            stdin = subprocess.PIPE
        )
        try:
            proc.stdin.write(bytes(text, "utf-8"))
        except TypeError:
            proc.stdin.write(text)
        proc.stdin.close()

    def classify(self, text):
        """ Instructs the classifier to categorize the text, and return the
        name of the category that best matches the text. """

        # need to escape path separator for the regex matching
        path = self.path.replace(os.sep, "\\%s" % os.sep)

        command = CRM_BINARY + (CLASSIFY_CMD % (CLASSIFICATION_TYPE,
                                                self.file_list_string(),
                                                path,
                                                CLASSIFICATION_EXT))

        proc = subprocess.Popen(
            command,
            shell = True,
            stdin = subprocess.PIPE,
            stdout = subprocess.PIPE
        )
        try:
            proc.stdin.write(bytes(text, "utf-8"))
            (output_list, err) = proc.communicate()
            output_list = output_list.decode("utf-8", "strict").split()
        except TypeError:
            proc.stdin.write(text)
            (output_list, err) = proc.communicate()
            output_list = output_list.split()

        proc.stdin.close()
        proc.stdout.close()

        if output_list is None:
            return ('', 0.0)
        else:
            category = output_list[0]
            probability = float(output_list[1])
            return (category, probability)

    def create_files(self):
        """ Ensures that the associated data files exist by learning an empty
        string. """

        # Create directory if necessary
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # Create category files
        for category in self.categories:
            self.learn(category, '')

    def file_list(self):
        """ Returns a list of classification files. """

        # Builds a file path given a category name
        def _file_path(category):
            return os.path.join(self.path, category + CLASSIFICATION_EXT)

        # Return list of all category paths
        return map(_file_path, self.categories)

    # return a list of classification files as a string
    def file_list_string(self):
        """ Returns a list of classification files as a string. """
        return ' '.join(self.file_list())

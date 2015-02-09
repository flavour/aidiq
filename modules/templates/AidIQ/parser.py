# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

""" Message Parsing

    Template-specific Message Parsers are defined here.

    @copyright: 2014-2015 (c) Sahana Software Foundation
    @license: MIT

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the "Software"), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.
"""

__all__ = ("S3Parser",)

from gluon import current

# =============================================================================
class S3Parser(object):
    """
       Message Parsing Template.
    """

    # -------------------------------------------------------------------------
    @staticmethod
    def _parse_value(text, fieldname):
        """
            Parse a value from a piece of text
        """

        parts = text.split(":%s:" % fieldname, 1)
        parts = parts[1].split(":", 1)
        result = parts[0]
        return result

    # -------------------------------------------------------------------------
    @staticmethod
    def parse_email(message):
        """
            Parse Responses
                - parse responses to mails from the Monitor service
        """

        db = current.db
        s3db = current.s3db
        reply = None

        # Need to use Raw currently as not showing in Body
        message_id = message.message_id
        table = s3db.msg_email
        record = db(table.message_id == message_id).select(table.raw,
                                                           limitby=(0, 1)
                                                           ).first()
        if not record:
            return reply

        message_body = record.raw
        if not message_body:
            return reply

        # What type of message is this?
        if ":run_id:" in message_body:
            # Response to Monitor Check

            # Parse Mail
            try:
                run_id = S3Parser._parse_value(message_body, "run_id")
                run_id = int(run_id)
            except:
                return reply

            # Update the Run entry to show that we have received the reply OK
            rtable = s3db.monitor_run
            db(rtable.id == run_id).update(status=1)
            return reply

        else:
            # Don't know what this is: ignore
            return reply

# END =========================================================================

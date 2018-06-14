"""
Copyright ©2018. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""


"""Logic for SIS enrollments API import job."""


from flask import current_app as app
from nessie.externals import sis_enrollments_api
from nessie.jobs.background_job import BackgroundJob
from nessie.lib.berkeley import sis_term_id_for_name


class ImportSisEnrollmentsApi(BackgroundJob):

    def run(self, csids):
        term_id = sis_term_id_for_name(app.config['CURRENT_TERM'])
        app.logger.info(f'Starting SIS enrollments API import job for term {term_id}, {len(csids)} students...')
        success_count = 0
        failure_count = 0
        for csid in csids:
            if sis_enrollments_api.get_drops_and_midterms(csid, term_id):
                success_count += 1
            else:
                failure_count += 1
                app.logger.error(f'SIS enrollments API import failed for CSID {csid}.')
        app.logger.info(f'SIS enrollments API import job completed: {success_count} succeeded, {failure_count} failed.')
        return True
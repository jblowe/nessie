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


from nessie.merged.sis_profile import get_holds, get_merged_sis_profile


class TestSisHolds:
    """Test SIS holds."""

    def test_no_holds(self, app):
        holds = get_holds('11667051')
        assert holds == []

    def test_multiple_holds(self, app):
        holds = get_holds('2345678901')
        assert len(holds) == 2
        assert holds[0]['reason']['code'] == 'CSBAL'
        assert holds[1]['reason']['code'] == 'ADVHD'

    def test_sid_not_found(self, app):
        holds = get_holds('99999')
        assert holds is False


class TestMergedSisProfile:
    """Test merged SIS profile."""

    def test_skips_concurrent_academic_status(self, app):
        """Skips concurrent academic status."""
        profile = get_merged_sis_profile('11667051')
        assert profile['academicCareer'] == 'UGRD'

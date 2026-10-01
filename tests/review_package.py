"""Focused deployment boundary tests without a database or delivery provider."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tele_tena import review, review_web


class Permission(Exception):
    pass


class ReviewPackage(unittest.TestCase):
    def setUp(self):
        def throw(*args):
            raise Permission()
        self.fake = SimpleNamespace(local=SimpleNamespace(site='review.test', request=None, response={}),
            conf={'tele_tena_review_site':'review.test', 'tele_tena_review_enabled':True},
            session=SimpleNamespace(user='Administrator'), PermissionError=Permission, throw=throw)
        self.context = patch.object(review, 'frappe', self.fake)
        self.context.start()
        self.addCleanup(self.context.stop)

    def test_site_binding_and_explicit_boolean(self):
        self.assertTrue(review.enabled())
        for key,value in [('tele_tena_review_site','customer.test'),('tele_tena_review_enabled','true'),('tele_tena_review_enabled',False)]:
            with patch.dict(self.fake.conf,{key:value}):
                self.assertFalse(review.enabled())
                with self.assertRaises(Permission):
                    review.cli()

    def test_configuration_refuses_development_or_csrf_bypass(self):
        for key in ('developer_mode', 'ignore_csrf'):
            with patch.dict(self.fake.conf, {key: True}):
                with self.assertRaises(ValueError):
                    review.configure()

    def test_not_http_even_for_administrator(self):
        self.fake.local.request = object()
        with self.assertRaises(Permission):
            review.cli()

    def test_not_nonadministrator(self):
        self.fake.session.user='reviewer@example.invalid'
        with self.assertRaises(Permission):
            review.cli()

    def test_invited_site_disables_contact_enrollment_uniformly(self):
        with self.assertRaises(Permission):
            review.guard_contact_access()
        self.assertEqual(self.fake.local.response['tele_tena_error'],'review_password_required')
        self.fake.conf.clear()
        review.guard_contact_access()

    def test_renderer_is_scoped(self):
        with patch.object(review_web,'enabled',return_value=True):
            for path in ('teletena','teletena/patient/appointments','teletena/sw.js'):
                self.assertTrue(review_web.ReviewPage(path).can_render())
            for path in ('api/method/login','assets/tele_tena/review/index.html','app','login','private/files/a.pdf','teletena-other'):
                self.assertFalse(review_web.ReviewPage(path).can_render())
        with patch.object(review_web,'enabled',return_value=False):
            self.assertFalse(review_web.ReviewPage('teletena').can_render())


if __name__ == '__main__':
    unittest.main(verbosity=2)

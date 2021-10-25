# Generated by Django 2.2.24 on 2021-10-23 19:57

from django.db import migrations

from emails.models import hash_subdomain


def delete_all_later_duplicate_subdomains(apps, schema_editor):
    Profile = apps.get_model('emails', 'Profile')
    RegisteredSubdomain = apps.get_model('emails', 'RegisteredSubdomain')
    profiles_with_subdomain = (
        Profile.objects.all().exclude(subdomain=None)
        .order_by('user__date_joined')
    )

    # find all duplicate subdomains
    duplicate_subdomains = set()
    for profile in profiles_with_subdomain:
        num_later_subdomain_registrations = Profile.objects.filter(
            subdomain__iexact=profile.subdomain, # check this
            user__date_joined__gt=profile.user.date_joined
        ).count()
        if num_later_subdomain_registrations > 0:
            duplicate_subdomains.add(profile.subdomain.lower())

    # remove duplicate subdomains
    for dupe in duplicate_subdomains:
        profile = Profile.objects.filter(
                subdomain__iexact=dupe
            ).order_by('user__date_joined').first()
        later_subdomain_registrations = Profile.objects.filter(
            subdomain__iexact=profile.subdomain,
            user__date_joined__gt=profile.user.date_joined
        )
        print('found case-insensitive duplicate subdomains of ' + \
            f'{profile.user.username}'
        )
        for dupe_subdomain_profile in later_subdomain_registrations:
            # empty out the subdomain of any new profiles that were
            # erroneously allowed to register a duplicate subdomain
            print('clearing subdomain for: ' + \
                f'{dupe_subdomain_profile.user.username}'
            )
            dupe_subdomain_profile.subdomain = None
            dupe_subdomain_profile.save()

    # lowercase all subdomains and
    # create RegisteredSubdomain for the lower cased subdomain
    reduced_profiles_with_subdomain = (
        Profile.objects.all().exclude(subdomain=None)
        .order_by('user__date_joined')
    )
    for oldest_profile in reduced_profiles_with_subdomain:
        # lowercase subdomain of every profile
        oldest_profile.subdomain = oldest_profile.subdomain.lower()
        oldest_profile.save()

        registered_subdomain_exists = RegisteredSubdomain.objects.filter(
            subdomain_hash=hash_subdomain(oldest_profile.subdomain)
        ).count() > 0
        if not registered_subdomain_exists:
            RegisteredSubdomain.objects.create(
                subdomain_hash=hash_subdomain(oldest_profile.subdomain)
            )


class Migration(migrations.Migration):

    dependencies = [
        ('emails', '0029_profile_add_deleted_metric_and_changeserver_storage_default'),
    ]

    operations = [
        migrations.RunPython(delete_all_later_duplicate_subdomains)
    ]
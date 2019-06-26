from gettext import gettext as _

from rest_framework import serializers

from pulpcore.plugin.models import Repository, RepositoryVersion
from pulpcore.plugin.serializers import (
    NoArtifactContentSerializer,
    SingleArtifactContentSerializer,
    RemoteSerializer,
    PublicationSerializer,
    PublicationDistributionSerializer,
    NestedRelatedField,
    validate_unknown_fields,
)

from pulp_rpm.app.models import (
    Modulemd,
    Package,
    RpmDistribution,
    RpmRemote,
    RpmPublication,
    UpdateRecord,
)

from pulp_rpm.app.fields import UpdateCollectionField, UpdateReferenceField


from pulp_rpm.app.constants import RPM_PLUGIN_TYPE_CHOICE_MAP


class PackageSerializer(SingleArtifactContentSerializer):
    """
    A Serializer for Package.

    Add serializers for the new fields defined in Package and add those fields to the Meta class
    keeping fields from the parent class as well. Provide help_text.
    """

    relative_path = serializers.CharField(
        help_text=_("File name of the package"),
        required=True,
        allow_null=True,
        allow_blank=True,
        write_only=True,
    )

    name = serializers.CharField(
        help_text=_("Name of the package"),
    )
    epoch = serializers.CharField(
        help_text=_("The package's epoch"),
        allow_blank=True, required=False,
    )
    version = serializers.CharField(
        help_text=_("The version of the package. For example, '2.8.0'"),
    )
    release = serializers.CharField(
        help_text=_("The release of a particular version of the package. e.g. '1.el7' or '3.f24'"),
    )
    arch = serializers.CharField(
        help_text=_("The target architecture for a package."
                    "For example, 'x86_64', 'i686', or 'noarch'"),
    )

    pkgId = serializers.CharField(
        help_text=_("Checksum of the package file"),
    )
    checksum_type = serializers.CharField(
        help_text=_("Type of checksum, e.g. 'sha256', 'md5'"),
    )

    summary = serializers.CharField(
        help_text=_("Short description of the packaged software"),
        allow_blank=True, required=False,
    )
    description = serializers.CharField(
        help_text=_("In-depth description of the packaged software"),
        allow_blank=True, required=False,
    )
    url = serializers.CharField(
        help_text=_("URL with more information about the packaged software"),
        allow_blank=True, required=False,
    )

    changelogs = serializers.CharField(
        help_text=_("Changelogs that package contains"),
        default="[]", required=False
    )
    files = serializers.CharField(
        help_text=_("Files that package contains"),
        default="[]", required=False
    )

    requires = serializers.CharField(
        help_text=_("Capabilities the package requires"),
        default="[]", required=False
    )
    provides = serializers.CharField(
        help_text=_("Capabilities the package provides"),
        default="[]", required=False
    )
    conflicts = serializers.CharField(
        help_text=_("Capabilities the package conflicts"),
        default="[]", required=False
    )
    obsoletes = serializers.CharField(
        help_text=_("Capabilities the package obsoletes"),
        default="[]", required=False
    )
    suggests = serializers.CharField(
        help_text=_("Capabilities the package suggests"),
        default="[]", required=False
    )
    enhances = serializers.CharField(
        help_text=_("Capabilities the package enhances"),
        default="[]", required=False
    )
    recommends = serializers.CharField(
        help_text=_("Capabilities the package recommends"),
        default="[]", required=False
    )
    supplements = serializers.CharField(
        help_text=_("Capabilities the package supplements"),
        default="[]", required=False
    )

    location_base = serializers.CharField(
        help_text=_("Base location of this package"),
        allow_blank=True, required=False
    )
    location_href = serializers.CharField(
        help_text=_("Relative location of package to the repodata"),
    )

    rpm_buildhost = serializers.CharField(
        help_text=_("Hostname of the system that built the package"),
        allow_blank=True, required=False
    )
    rpm_group = serializers.CharField(
        help_text=_("RPM group (See: http://fedoraproject.org/wiki/RPMGroups)"),
        allow_blank=True, required=False
    )
    rpm_license = serializers.CharField(
        help_text=_("License term applicable to the package software (GPLv2, etc.)"),
        allow_blank=True, required=False
    )
    rpm_packager = serializers.CharField(
        help_text=_("Person or persons responsible for creating the package"),
        allow_blank=True, required=False
    )
    rpm_sourcerpm = serializers.CharField(
        help_text=_("Name of the source package (srpm) the package was built from"),
        allow_blank=True, required=False
    )
    rpm_vendor = serializers.CharField(
        help_text=_("Name of the organization that produced the package"),
        allow_blank=True, required=False
    )
    rpm_header_start = serializers.IntegerField(
        help_text=_("First byte of the header"),
    )
    rpm_header_end = serializers.IntegerField(
        help_text=_("Last byte of the header"),
    )

    size_archive = serializers.IntegerField(
        help_text=_("Size, in bytes, of the archive portion of the original package file")
    )
    size_installed = serializers.IntegerField(
        help_text=_("Total size, in bytes, of every file installed by this package")
    )
    size_package = serializers.IntegerField(
        help_text=_("Size, in bytes, of the package")
    )

    time_build = serializers.IntegerField(
        help_text=_("Time the package was built in seconds since the epoch")
    )
    time_file = serializers.IntegerField(
        help_text=_("The 'file' time attribute in the primary XML - "
                    "file mtime in seconds since the epoch.")
    )

    def validate(self, data):
        """
        Validate the rpm package data.

        Args:
            data (dict): Data to be validated

        Returns:
            dict: Data that has been validated

        """
        data = super().validate(data)

        data['_relative_path'] = data.pop('relative_path')

        return data

    class Meta:
        fields = tuple(set(SingleArtifactContentSerializer.Meta.fields) - {'_relative_path'}) + (
            'name', 'epoch', 'version', 'release', 'arch', 'pkgId', 'checksum_type',
            'summary', 'description', 'url', 'changelogs', 'files',
            'requires', 'provides', 'conflicts', 'obsoletes',
            'suggests', 'enhances', 'recommends', 'supplements',
            'location_base', 'location_href',
            'rpm_buildhost', 'rpm_group', 'rpm_license',
            'rpm_packager', 'rpm_sourcerpm', 'rpm_vendor',
            'rpm_header_start', 'rpm_header_end',
            'size_archive', 'size_installed', 'size_package',
            'time_build', 'time_file', 'relative_path'
        )
        model = Package


class MinimalPackageSerializer(PackageSerializer):
    """
    A minimal serializer for RPM packages.
    """

    class Meta:
        fields = SingleArtifactContentSerializer.Meta.fields + (
            'name', 'epoch', 'version', 'release', 'arch', 'pkgId', 'checksum_type',
        )
        model = Package


class RpmRemoteSerializer(RemoteSerializer):
    """
    A Serializer for RpmRemote.
    """

    class Meta:
        fields = RemoteSerializer.Meta.fields
        model = RpmRemote


class RpmPublicationSerializer(PublicationSerializer):
    """
    A Serializer for RpmPublication.
    """

    class Meta:
        fields = PublicationSerializer.Meta.fields
        model = RpmPublication


class UpdateRecordSerializer(NoArtifactContentSerializer):
    """
    A Serializer for UpdateRecord.
    """

    id = serializers.CharField(
        help_text=_("Update id (short update name, e.g. RHEA-2013:1777)")
    )
    updated_date = serializers.CharField(
        help_text=_("Date when the update was updated (e.g. '2013-12-02 00:00:00')")
    )

    description = serializers.CharField(
        help_text=_("Update description")
    )
    issued_date = serializers.CharField(
        help_text=_("Date when the update was issued (e.g. '2013-12-02 00:00:00')")
    )
    fromstr = serializers.CharField(
        help_text=_("Source of the update (e.g. security@redhat.com)")
    )
    status = serializers.CharField(
        help_text=_("Update status ('final', ...)")
    )
    title = serializers.CharField(
        help_text=_("Update name")
    )
    summary = serializers.CharField(
        help_text=_("Short summary")
    )
    version = serializers.CharField(
        help_text=_("Update version (probably always an integer number)")
    )

    type = serializers.CharField(
        help_text=_("Update type ('enhancement', 'bugfix', ...)")
    )
    severity = serializers.CharField(
        help_text=_("Severity")
    )
    solution = serializers.CharField(
        help_text=_("Solution")
    )
    release = serializers.CharField(
        help_text=_("Update release")
    )
    rights = serializers.CharField(
        help_text=_("Copyrights")
    )

    pushcount = serializers.CharField(
        help_text=_("Push count")
    )

    pkglist = UpdateCollectionField(
        source='pk', read_only=True,
        help_text=_("List of packages")
    )
    references = UpdateReferenceField(
        source='pk', read_only=True,
        help_text=_("List of references")
    )

    class Meta:
        fields = NoArtifactContentSerializer.Meta.fields + (
            'id', 'updated_date', 'description', 'issued_date',
            'fromstr', 'status', 'title', 'summary', 'version',
            'type', 'severity', 'solution', 'release', 'rights',
            'pushcount', 'pkglist', 'references'
        )
        model = UpdateRecord


class MinimalUpdateRecordSerializer(UpdateRecordSerializer):
    """
    A minimal serializer for RPM update records.
    """

    class Meta:
        fields = NoArtifactContentSerializer.Meta.fields + (
            'id', 'title', 'severity', 'type'
        )
        model = UpdateRecord


class OneShotUploadSerializer(serializers.Serializer):
    """
    A serializer for the One Shot Upload API.
    """

    repository = serializers.HyperlinkedRelatedField(
        help_text=_('A URI of the repository.'),
        required=False,
        queryset=Repository.objects.all(),
        view_name='repositories-detail',
    )
    file = serializers.FileField(
        help_text=_("The rpm file."),
        required=True,
    )


class RpmDistributionSerializer(PublicationDistributionSerializer):
    """
    Serializer for RPM Distributions.
    """

    class Meta:
        fields = PublicationDistributionSerializer.Meta.fields
        model = RpmDistribution


class CopySerializer(serializers.Serializer):
    """
    A serializer for Content Copy API.
    """

    source_repo = serializers.HyperlinkedRelatedField(
        help_text=_('A URI of the repository.'),
        required=False,
        queryset=Repository.objects.all(),
        view_name='repositories-detail',
    )
    source_repo_version = NestedRelatedField(
        help_text=_('A URI of the repository version'),
        required=False,
        queryset=RepositoryVersion.objects.all(),
        parent_lookup_kwargs={'repository_pk': 'repository__pk'},
        lookup_field='number',
        view_name='versions-detail',
    )
    dest_repo = serializers.HyperlinkedRelatedField(
        help_text=_('A URI of the repository.'),
        required=True,
        queryset=Repository.objects.all(),
        view_name='repositories-detail',
    )
    types = serializers.ListField(
        help_text=_('A list of types to copy ["package", "advisory"]'),
        write_only=True,
        default=['package', 'advisory']
    )

    def validate(self, data):
        """
        Validate that the Serializer contains valid data.

        Set the Repository based on the RepositoryVersion if only the latter is provided.
        Set the RepositoryVersion based on the Repository if only the latter is provied.
        Convert the human-friendly names of the content types into what Pulp needs to query on.

        """
        super().validate(data)
        if hasattr(self, 'initial_data'):
            validate_unknown_fields(self.initial_data, self.fields)

        new_data = {}
        new_data.update(data)

        source_repo = data.get('source_repo')
        source_repo_version = data.get('source_repo_version')

        if not source_repo and not source_repo_version:
            raise serializers.ValidationError(
                _("Either the 'source_repo' or 'source_repo_version' need to be specified"))

        if source_repo and source_repo_version:
            raise serializers.ValidationError(
                _("Either the 'source_repo' or 'source_repo_version' need to be specified "
                  "but not both.")
            )

        if not source_repo and source_repo_version:
            repo = {'source_repo': source_repo_version.repository}
            new_data.update(repo)

        if source_repo and not source_repo_version:
            version = RepositoryVersion.latest(source_repo)
            if version:
                repo_version = {'source_repo_version': version}
                new_data.update(repo_version)
            else:
                raise serializers.ValidationError(
                    detail=_('Repository has no version available to copy'))

        types = data.get('types')
        final_types = []

        if types:
            for t in types:
                substitution = RPM_PLUGIN_TYPE_CHOICE_MAP.get(t)
                if not substitution:
                    raise serializers.ValidationError(_(
                        "'{type}' is an invalid type, please use one of {choices}".format(
                            type=t,
                            choices=list(RPM_PLUGIN_TYPE_CHOICE_MAP.keys())
                        ))
                    )
                final_types.append(substitution)
            new_data.update({'types': final_types})

        return new_data


class ModulemdSerializer(SingleArtifactContentSerializer):
    """
    Modulemd serializer.
    """
    name = serializers.CharField(
        help_text=_("Modulemd name."),
    )
    stream = serializers.CharField(
        help_text=_("Stream name."),
    )
    version = serializers.CharField(
        help_text=_("Modulemd version."),
    )
    context = serializers.CharField(
        help_text=_("Modulemd context."),
    )
    arch = serializers.CharField(
        help_text=_("Modulemd architecture."),
    )
    artifacts = serializers.CharField(
        help_text=_("Modulemd artifacts (rpm packages)."),
        allow_null=True
    )
    dependencies = serializers.CharField(
        help_text=_("Modulemd dependencies."),
        allow_null=True
    )
    packages = serializers.PrimaryKeyRelatedField(
        help_text=_("Pulp connected packages."),
        allow_null=True,
        required=False,
        queryset=Package.objects.all(),
        many=True
    )

    def create(self, validated_data):
        modulemd = Modulemd.objects.create(**validated_data)
        # scan for pkgs, will be refactored elsewhere
        pkgs = modulemd.packages_to_pkg_ver()
        missing = []  # info for user to know he's missing packages
        for pkg in pkgs:
            try:
                p = Package.objects.get(name=pkg[0], version=pkg[1])
                modulemd.packages.add(p)
            except Exception:
                missing.append(pkg)
        return modulemd

    class Meta:
        fields = (
            'name', 'stream', 'version', 'context', 'arch',
            'artifacts', 'dependencies', 'packages'
        )
        model = Modulemd

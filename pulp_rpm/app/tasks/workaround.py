from django.db.models import Prefetch, prefetch_related_objects

from pulpcore.plugin.stages import RemoteArtifactSaver
from pulpcore.plugin.models import ContentArtifact, RemoteArtifact

from gettext import gettext as _


class RPMRemoteArtifactSaver(RemoteArtifactSaver):
    """Workaround until relative_path issue will be solved."""
    def _needed_remote_artifacts(self, batch):
        """
        Build a list of only :class:`~pulpcore.plugin.models.RemoteArtifact` that need
        to be created for the batch.

        Args:
            batch (list): List of :class:`~pulpcore.plugin.stages.DeclarativeContent`.

        Returns:
            List: Of :class:`~pulpcore.plugin.models.RemoteArtifact`.
        """
        remotes_present = set()
        for d_content in batch:
            for d_artifact in d_content.d_artifacts:
                if d_artifact.remote:
                    remotes_present.add(d_artifact.remote)

        prefetch_related_objects(
            [d_c.content for d_c in batch],
            Prefetch(
                "contentartifact_set",
                queryset=ContentArtifact.objects.prefetch_related(
                    Prefetch(
                        "remoteartifact_set",
                        queryset=RemoteArtifact.objects.filter(remote__in=remotes_present),
                        to_attr="_remote_artifact_saver_ras",
                    )
                ),
                to_attr="_remote_artifact_saver_cas",
            ),
        )
        needed_ras = []
        for d_content in batch:
            for content_artifact in d_content.content._remote_artifact_saver_cas:
                for d_artifact in d_content.d_artifacts:
                    if d_artifact.relative_path == content_artifact.relative_path:
                        break
                    else:
                        if getattr(content_artifact.content, 'data_type', False) == 'productid' \
                                and content_artifact.relative_path:
                            d_artifact.relative_path = content_artifact.relative_path
                            break
                else:
                    msg = _('No declared artifact with relative path "{rp}" for content "{c}"')
                    raise ValueError(
                        msg.format(rp=content_artifact.relative_path, c=d_content.content)
                    )
                for remote_artifact in content_artifact._remote_artifact_saver_ras:
                    if remote_artifact.remote_id == d_artifact.remote.pk:
                        break
                else:
                    if d_artifact.remote:
                        remote_artifact = self._create_remote_artifact(d_artifact, content_artifact)
                        needed_ras.append(remote_artifact)
        return needed_ras

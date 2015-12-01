from conans.errors import ConanException
from conans.operations import DiskRemover


class ConanRemover(object):
    """ Class responsible for removing locally/remotely conans, package folders, etc. """

    def __init__(self, file_manager, user_io, remote_manager, remote=None):
        self._user_io = user_io
        self._remote_manager = remote_manager
        self._remote = remote
        self._file_manager = file_manager

    def remove(self, pattern, src=None, build_ids=None, package_ids_filter=None, force=False):
        """ Remove local/remote conans, package folders, etc.
        @param pattern: it could be OpenCV* or OpenCV
        @param package_ids_filter: Lists with ids or empty for all. (Its a filter)
        @param force: if True, it will be deleted without requesting anything
        """

        if self._remote:
            if build_ids is not None or src:
                raise ConanException("Remotes don't have 'build' or 'src' folder, just packages")
            search_info = self._remote_manager.search(pattern, remote=self._remote)
        else:
            search_info = self._file_manager.search(pattern)

        if not search_info:
            self._user_io.out.warn("No conans reference matches with %s pattern" % pattern)
            return

        for conan_ref in search_info:
            if self._ask_permission(conan_ref, src, build_ids, package_ids_filter, force):
                if self._remote:
                    if package_ids_filter is None:
                        self._remote_manager.remove(conan_ref, self._remote)
                    else:
                        self._remote_manager.remove_packages(conan_ref, package_ids_filter,
                                                             self._remote)
                else:
                    remover = DiskRemover(self._file_manager.paths)
                    if src:
                        remover.remove_src(conan_ref)
                    if build_ids is not None:
                        remover.remove_builds(conan_ref, build_ids)
                    if package_ids_filter is not None:
                        remover.remove_packages(conan_ref, package_ids_filter)
                    if not src and build_ids is None and package_ids_filter is None:
                        remover.remove(conan_ref)

    def _ask_permission(self, conan_ref, src, build_ids, package_ids_filter, force):
        if force:
            return True
        aux_str = []
        if src:
            aux_str.append(" src folder")
        if build_ids is not None:
            if build_ids:
                aux_str.append(" %s builds" % build_ids)
            else:
                aux_str.append(" all builds")
        if package_ids_filter is not None:
            if package_ids_filter:
                aux_str.append(" %s package" % package_ids_filter)
            else:  # All packages to remove, no filter
                aux_str.append(" all packages")
        return self._user_io.request_boolean("Are you sure you want to delete%s from '%s'"
                                             % (", ".join(aux_str), str(conan_ref)))

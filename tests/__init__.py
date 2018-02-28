import os

from rollbackable_procedure.rollbackable_procedure import RollbackableProcedure, revertable_task


os.chdir(os.path.dirname(__file__))


class GenerateDirsWithFiles(RollbackableProcedure):
    """A base procedure to create a directory, insert files with content into it and rename them.
    """
    def __init__(self, dir_name):
        self.dir_name = dir_name
        super(GenerateDirsWithFiles, self).__init__()

    def full_path(self, file_name):
        return os.path.join(self.dir_name, file_name)

    @revertable_task
    def create_dir(self):
        os.mkdir(self.dir_name)

    @create_dir.reverter
    def create_dir(self):
        os.rmdir(self.dir_name)

    @revertable_task
    def insert_file(self, file_name, content):
        with open(self.full_path(file_name), 'w') as f:
            f.write(content)

    @insert_file.reverter
    def insert_file(self, file_name):
        os.remove(self.full_path(file_name))

    @revertable_task
    def rename_file(self, file_name, new_file_name):
        file_name, new_file_name = self.full_path(file_name), self.full_path(new_file_name)
        os.rename(file_name, new_file_name)

    @rename_file.reverter
    def rename_file(self, new_file_name, file_name):
        # We are flipping the args order in order to test the functionality of the arguments positioning
        # Described in revertable_task.reverter
        file_name, new_file_name = self.full_path(file_name), self.full_path(new_file_name)
        os.rename(new_file_name, file_name)


class GenerateDirsWithFiles__success(GenerateDirsWithFiles):
    def perform(self):
        self.create_dir()
        for i in 'abc':
            self.insert_file('{}.txt'.format(i), 'Hello {}'.format(i))
        self.rename_file('c.txt', 'd.txt')


class GenerateDirsWithFiles__failure(GenerateDirsWithFiles):

    @revertable_task
    def raise_here(self):
        raise

    @raise_here.reverter
    def raise_here(self):
        pass

    def perform(self):
        self.create_dir()
        for i in 'abc':
            self.insert_file('{}.txt'.format(i), 'Hello {}'.format(i))
        self.rename_file('c.txt', 'd.txt')
        self.raise_here()
        self.insert_file('e')
        self.insert_file('f')
        self.insert_file('g')


def test_passed_procedure():
    my_dir = 'my_dir'
    proc = GenerateDirsWithFiles__success(my_dir)
    proc.run()
    # Verifying that everything is done
    assert os.path.isdir(my_dir)
    for i in 'abd':
        assert os.path.exists('{}/{}.txt'.format(my_dir, i))
    proc.rollback()
    # Verifying that everything is rolled back
    assert not os.path.isdir(my_dir)
    for i in 'abcd':
        assert not os.path.exists('{}/{}.txt'.format(my_dir, i))


def test_failed_procedure():

    my_dir = 'my_dir'
    proc = GenerateDirsWithFiles__failure(my_dir)
    proc.run()
    # Verifying that the the rollback indeed happened in the right place and revert the right functions
    assert proc.actions_log == [
        [proc.create_dir.action, tuple(), {}],
        [proc.insert_file.action, ('a.txt', 'Hello a'), {}],
        [proc.insert_file.action, ('b.txt', 'Hello b'), {}],
        [proc.insert_file.action, ('c.txt', 'Hello c'), {}],
        [proc.rename_file.action, ('c.txt', 'd.txt'), {}],
        [proc.raise_here.action, tuple(), {}],
        [proc.raise_here.revert, tuple(), {}],
        [proc.rename_file.revert, ('d.txt', 'c.txt'), {}],
        [proc.insert_file.revert, ('c.txt',), {}],
        [proc.insert_file.revert, ('b.txt',), {}],
        [proc.insert_file.revert, ('a.txt',), {}],
        [proc.create_dir.revert, tuple(), {}],
    ]
    # Verifying that everything is reverted
    assert not os.path.isdir(my_dir)
    for i in 'abc':
        assert not os.path.exists('{}/{}.txt'.format(my_dir, i))

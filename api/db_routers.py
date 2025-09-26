class PrimaryReplicaRouter:
    """
    A router to send all write operations to the default (primary) database
    and all read operations to the read_replica database.
    """

    def db_for_read(self, model, **hints):
        """Direct all read operations to the read_replica database."""
        return 'read_replica'

    def db_for_write(self, model, **hints):
        """Direct all write operations to the default database."""
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations between objects in the primary database."""
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Only allow migrations on the primary database."""
        return db == 'default'
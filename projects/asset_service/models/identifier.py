# -- identifier.py --

# model of an identifier, alteternative unique ID of an asset

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

# -- external dependencies --
from uuid import UUID, uuid4
from sqlalchemy import orm
from sqlalchemy.sql import func
import sqlalchemy.dialects.postgresql as pgtypes

# -- project dependencies --
from . import db, BaseModel
from .attribute import AttributeType, Attribute


class IdentifierType(AttributeType):
    """Identifier Types

    to allow for plausibility checks and connect to external resources,
    identifiers can be grouped in types. This also allows to handle Identifiers
    appropriate in a user interface.
    """

    @orm.reconstructor
    def reconstruct(self):
        self.regex = None


    __mapper_args__ = {
        'polymorphic_identity': True
    }


class Identifier(Attribute):
    """Alternative Identifiers

    While an asset is primarily identified by its UUID, it can also have multiple additional
    identifiers that are managed by auxiliary systems.
    Additional identifiers have to be unique and can therefore be used to identify assets
    distinctly.

    #### Examples
     * serial numbers (but they must be globally unique within the tenant)
     * license plates
     * identifiers issued by other asset management systems, such as asset-tags / labels
     * RFID serial numbers

    #### String representation
    The current implementation allows to handle identifiers that can be represented
    as a string with a maximum length of 40 characters. The application limits this
    to printable ASCII characters (ASCII 0x20 to 0x7E).
    Future implementations might distinguish between `id_str` and e.g. `id_int` or `id_rfid` etc.

    #### types
    By defining a typename, additional features such as validity checks based on
    regular expressions or links to external resources can be realized.
    """

    asset = db.relation(
        'Asset',
        backref = db.backref('identifiers', lazy=True)
    )
    
    @orm.reconstructor
    def reconstruct(self):
        self.id_str = self.value

    __mapper_args__ = {
        'polymorphic_identity': True
    }

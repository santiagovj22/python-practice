# --meta_source.py --

# model of a sophia meta_source table

# EKU Power Drives GmbH 2021, Matthias Epple <matthias.epple@ekupd.com>

# -- external depenencies --
import sqlalchemy.dialects.postgresql as pgtypes

# -- project dependencies --
from . import db, BaseModel

class MetaSource(BaseModel):
    
    __tablename__ = 'meta_source'
    __table_args__ = ({'schema': 'public'})
    
    id = db.Column( pgtypes.BIGINT, primary_key=True )
    source = db.Column( pgtypes.JSONB ) # this is the actual source data stored as a JSON file

    @classmethod
    def getSourceIdFromFatnodeUUID(cls, fatnode_uuid):    
        ''' return the meta_source id's identified by the given fatnode_uuid'''
        return cls.query.filter(cls.source["fatnode"].astext.cast(pgtypes.UUID) == fatnode_uuid)

    @classmethod
    def create(cls, **kwargs):
        kwargs = {k:v for k,v in kwargs.items() if hasattr(cls, k)}
        source = cls(**kwargs)
        db.session.add(source)
        db.session.commit()
        return source

    # don't do it like this! 
    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e


# --meta_quality.py --

# model of a sophia meta_source table

# EKU Power Drives GmbH 2021, Matthias Epple <matthias.epple@ekupd.com>

# -- external depenencies --
import sqlalchemy.dialects.postgresql as pgtypes

# -- project dependencies --
from . import db, BaseModel

class MetaQuality(BaseModel):
    
    __tablename__ = 'meta_quality'
    __table_args__ = ({'schema': 'public'})

    
    id = db.Column( pgtypes.BIGINT, primary_key=True )
    quality = db.Column( pgtypes.JSONB )     # this is the actual source data stored as a JSON file

    # don't do it like this! 
    def save(self):
        db.session.add(self)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e
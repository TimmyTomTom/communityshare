from datetime import datetime
import logging

from sqlalchemy import Column, Integer, String, DateTime, Boolean, and_, or_
from sqlalchemy import ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship, backref

import passlib
from passlib import context

from community_share import store, Base, config
from community_share.models.base import Serializable
from community_share.models.secret import Secret
from community_share.models.search import Search
from community_share.models.institution import InstitutionAssociation


logger = logging.getLogger(__name__)

class User(Base, Serializable):
    __tablename__ = 'user'

    MANDATORY_FIELDS = ['name', 'email']
    WRITEABLE_FIELDS = ['name', 'is_administrator', 'institution_associations',
                        'zipcode', 'website', 'twitter_handle', 'linkedin_link',
                        'year_of_birth', 'gender', 'ethnicity', 'bio']
    STANDARD_READABLE_FIELDS = [
        'id', 'name', 'is_administrator', 'last_active', 'is_educator',
        'is_community_partner', 'institution_associations',
        'zipcode', 'website', 'twitter_handle', 'linkedin_link',
        'year_of_birth', 'gender', 'ethnicity', 'bio', 'picture_url',
        'email_confirmed', 'active']

    ADMIN_READABLE_FIELDS = [
        'id', 'name', 'email' , 'date_created', 'last_active',
        'is_administrator', 'is_educator', 'is_community_partner',
        'institution_associations',
        'zipcode', 'website', 'twitter_handle', 'linkedin_link',
        'year_of_birth', 'gender', 'ethnicity', 'bio', 'picture_url',
        'email_confirmed', 'active'
    ]

    PERMISSIONS = {
        'all_can_read_many': False,
        'standard_can_read_many': False,
        'admin_can_delete': True
    }
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
    email_confirmed = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, default=True)
    password_hash = Column(String(120), nullable=True)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_inactivated = Column(DateTime, nullable=True)
    is_administrator = Column(Boolean, nullable=False, default=False) 
    last_active = Column(DateTime)

    picture_filename = Column(String(100))
    bio = Column(String(1000))
    zipcode = Column(String(50))
    website = Column(String(100))
    twitter_handle = Column(String(100))
    linkedin_link = Column(String(100))
    year_of_birth = Column(Integer)
    gender = Column(String(100))
    ethnicity = Column(String(100))
    
    searches = relationship("Search", backref="searcher_user")
    institution_associations = relationship("InstitutionAssociation")

    pwd_context = passlib.context.CryptContext(
        schemes=['sha512_crypt'],
        default='sha512_crypt',
        all__vary_rounds = 0.1,
        sha512_crypt__vary_rounds = 8000,
    )
    
    def searches_as(self, role):
        searches = store.session.query(Search).filter_by(
            searcher_user_id=self.id, searcher_role=role).all()
        return searches

    @property
    def confirmed_email(self):
        output = None
        if self.email_confirmed:
            output = self.email
        return output
        
    @property
    def is_educator(self):
        output = (len(self.searches_as('educator')) > 0)
        return output

    @property
    def is_community_partner(self):
        output = (len(self.searches_as('partner')) > 0)
        return output

    def is_password_correct(self, password):
        if not self.password_hash:
            is_correct = False
        else:
            is_correct = self.pwd_context.verify(password, self.password_hash)
        return is_correct

    @classmethod
    def is_password_valid(cls, password):
        error_messages = []
        if len(password) < 8:
            error_messages.append(
                'Password must have a length of at least 8 characters')
        return error_messages

    def set_password(self, password):
        output = None
        error_messages = self.is_password_valid(password)
        if not error_messages:
            password_hash = User.pwd_context.encrypt(password)
            self.password_hash = password_hash
        return error_messages

    def __repr__(self):
        output = "<User(email={email})>".format(email=self.email) 
        return output

    @classmethod
    def has_add_rights(cls, data, user):
        return False

    def has_admin_rights(self, user):
        has_admin_rights = False
        if user is not None:
            if user.is_administrator:
                has_admin_rights = True
            elif user.id == self.id:
                has_admin_rights = True
        return has_admin_rights

    def serialize_institution_associations(self, requester):
        associations = [i.serialize(requester)
                        for i in self.institution_associations]
        return associations

    def serialize_picture_url(self, requester):
        url = ''
        if (config.UPLOAD_LOCATION is not None) and self.picture_filename:
            url = config.UPLOAD_LOCATION + self.picture_filename
        return url

    custom_serializers = {
        'institution_associations': serialize_institution_associations,
        'picture_url': serialize_picture_url,
    }
         
    def deserialize_institution_associations(self, data_list):
        if data_list is None:
            data_list = []
        data_list = [d for d in data_list if d != {}]
        self.institution_associations = [
            InstitutionAssociation.admin_deserialize(data) for data in data_list]
        for ia in self.institution_associations:
            ia.user = self

    custom_deserializers = {
        'institution_associations': deserialize_institution_associations,
        }

    def make_api_key(self):
        secret_data = {
            'userId': self.id,
            'action': 'api_key',
        }
        secret = Secret.create_secret(info=secret_data, hours_duration=24)
        return secret
        
    @classmethod
    def from_api_key(self, key):
        secret = Secret.lookup_secret(key)
        logger.debug('key is {0}'.format(key))
        logger.debug('secret is {0}'.format(secret))
        user_id = None
        if secret is not None:
            info = secret.get_info()
            if info.get('action', None) == 'api_key':
                user_id = info.get('userId', None)
        if user_id is not None:
            user = store.session.query(User).filter_by(id=user_id).first()
            logger.debug('user from api_key is {0}'.format(user))
        else:
            user = None
        return user

    def on_delete(self, requester):
        # Importing here to prevent circular reference
        from community_share import mail_actions
        from community_share.models.share import Event, Share
        mail_actions.send_account_deletion_message(self)
        # Delete all upcoming events.
        upcoming_events = store.session.query(Event).filter(
            and_(Event.active==True,
                 or_(Share.educator_user_id==self.id,
                     Share.community_partner_user_id==self.id)))
        shares = set([])
        for event in upcoming_events:
            event.delete(requester)
            shares.add(event.share)
        for share in shares:
            other_user = None
            if share.educator_user_id == self.id:
                other_user = share.community_partner
            elif share.community_partner_user_id == self.id:
                other_user = share.educator
            mail_actions.send_partner_deletion_message(
                other_user, self, share.conversation)

class UserReview(Base, Serializable):
    __tablename__ = 'userreview'
    
    MANDATORY_FIELDS = [
        'user_id', 'rating', 'creator_user_id', 'event_id']
    WRITEABLE_FIELDS = [
        'review']
    STANDARD_READABLE_FIELDS = [
        'id', 'user_id', 'rating', 'review'
    ]
    ADMIN_READABLE_FIELDS = [
        'id', 'user_id', 'rating', 'review'
    ]

    PERMISSIONS = {
        'all_can_read_many': False,
        'standard_can_read_many': False,
        'admin_can_delete': False
    }
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    event_id = Column(Integer, ForeignKey('event.id'))
    rating = Column(Integer, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    creator_user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    review = Column(String(5000))

    __table_args__ = (
        CheckConstraint('rating>=0', 'Rating is negative'),
        CheckConstraint('rating<=5', 'Rating is greater than 5'),
    )

    event = relationship('Event')
    user = relationship('User', primaryjoin='UserReview.user_id == User.id')
    creator_user = relationship('User', primaryjoin='UserReview.creator_user_id == User.id')


    @classmethod
    def has_add_rights(cls, data, requester):
        from community_share.models.share import Event
        has_rights = False
        data['creator_user_id'] = requester.id
        event_id = int(data.get('event_id', -1))
        user_id = int(data.get('user_id', -1))
        event = store.session.query(Event).filter(Event.id==event_id).first()
        now = datetime.utcnow()
        if event.active and event.datetime_start < now:
            event_users = set([event.share.educator_user_id,
                               event.share.community_partner_user_id])
            request_users = set([requester.id, user_id])
            if event_users == request_users:
                already_exists = store.session.query(UserReview).filter(and_(
                    UserReview.user_id==user_id,
                    UserReview.creator_user_id==requester.id,
                    UserReview.event_id==event_id)).count()
                total = store.session.query(UserReview).count()
                logger.debug('Review already existing = {} total={}'.format(already_exists, total))
                if not already_exists:
                    has_rights = True
        return has_rights

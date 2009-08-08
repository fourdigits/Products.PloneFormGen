"""fieldset -- A fieldset container for form fields"""

__author__  = 'Steve McMahon <steve@dcn.org>'
__docformat__ = 'plaintext'

from types import BooleanType

from zope.interface import implements, providedBy

import logging

from AccessControl import ClassSecurityInfo
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFCore.utils import getToolByName

from Products.CMFPlone.utils import safe_hasattr, base_hasattr

from Products.Archetypes.public import *

from Products.ATContentTypes.content.folder import ATFolderSchema, ATFolder
from Products.ATContentTypes.content.schemata import finalizeATCTSchema
from Products.ATContentTypes.content.base import registerATCT

from Products.PloneFormGen.config import *
from Products.PloneFormGen.widgets import \
    FieldsetStartWidget, FieldsetEndWidget

from Products.PloneFormGen.interfaces import IPloneFormGenFieldset
from Products.PloneFormGen import PloneFormGenMessageFactory as _

import zope.i18n

FieldsetFolderSchema = ATFolderSchema.copy() + Schema((
    BooleanField('useLegend',
        required=0,
        searchable=0,
        default='1',
        widget=BooleanWidget(label='Show Title as Legend',
            label_msgid = "label_showlegend_text",
            description_msgid = "help_showlegend_text",
            i18n_domain = "ploneformgen",
            ),
        ),
    StringField('conditionalField',
                required=0,
                searchable=0,
                widget=SelectionWidget(label='Conditional Field',
                                       description='Optionally select the field to be evaluated as the condition for this fieldset.',
                                       label_msgid = "label_conditionalfield_text",
                                       description_msgid = "help_conditionalfield_text",
                                       i18n_domain = "ploneformgen",
                                       ),
                vocabulary='conditionalFieldDL',
                ),
    StringField('conditionalFieldValue',
                required=0,
                searchable=0,
                widget=StringWidget(label='Conditional Field Value',
                                    description='If you choose a conditional field, enter the value here such that the condition is evaluated as true.',
                                    label_msgid = "label_conditionalfieldvalue_text",
                                    description_msgid = "help_conditionalfieldvalue_text",
                                    i18n_domain = "ploneformgen",
                                    ),
                ),
    ))

FieldsetFolderSchema['description'].widget.label = 'Fieldset Help'
FieldsetFolderSchema['description'].widget.i18n_domain = 'ploneformgen'
FieldsetFolderSchema['description'].widget.label_msgid = 'label_fieldsethelp_text'
FieldsetFolderSchema['description'].widget.description = None
FieldsetFolderSchema['description'].widget.description_msgid = None
FieldsetFolderSchema.moveField('description', after='useLegend')


class FieldsetFolder(ATFolder):
    """A folder which groups form fields as a fieldset."""
    implements(IPloneFormGenFieldset)
    
    schema         =  FieldsetFolderSchema

    content_icon   = 'Fieldset.gif'
    meta_type      = 'FieldsetFolder'
    portal_type    = 'FieldsetFolder'
    archetype_name = 'Fieldset Folder'
    suppl_views = ()

    typeDescription= 'A folder which groups form fields as a fieldset.'

    global_allow = 0    

    # XXX We should do this with a tool so that others may add fields
    allowed_content_types = fieldTypes

    security       = ClassSecurityInfo()


    def __init__(self, oid, **kwargs):
        """ initialize class """

        ATFolder.__init__(self, oid, **kwargs)
        
        self.fsStartField = StringField('FieldSetStart',
            searchable=0,
            required=0,
            write_permission = View,
            widget=FieldsetStartWidget(),
            )
        

        self.fsEndField = StringField('FieldSetEnd',
            searchable=0,
            required=0,
            write_permission = View,
            widget=FieldsetEndWidget(),
            )
        

    security.declareProtected(ModifyPortalContent, 'setTitle')
    def setTitle(self, value, **kw):
        """ set title of object and field label """

        self.title = value
        self.fsStartField.widget.label = value


    security.declareProtected(ModifyPortalContent, 'setDescription')
    def setDescription(self, value, **kw):
        """ set description for field widget """

        self.fsStartField.widget.description = value
        self.getField('description').set(self, value, **kw)


    security.declareProtected(ModifyPortalContent, 'setDescription')
    def setUseLegend(self, value, **kw):
        """ set useLegend as attribute and widget attribute """
        if type(value) == BooleanType:
            self.fsStartField.widget.show_legend = value
            self.useLegend = value
        else:
            self.fsStartField.widget.show_legend = value == '1' or value == 'True'
            self.useLegend = value == '1' or value == 'True'


    security.declarePrivate('fieldsetFields')
    def fieldsetFields(self, objTypes=None, includeFSMarkers=False):
        """ 
        return list of enclosed fields;
        if includeFSMarkers, include markers for fieldset start/end
        """

        myObjs = []
        if includeFSMarkers:
            myObjs.append(self.fsStartField)

        for obj in self.objectValues(objTypes):
            # use shasattr to make sure we're not aquiring
            # fgField by acquisition
            if base_hasattr(obj, 'fgField'):
                myObjs.append(obj)

        if includeFSMarkers:
            myObjs.append(self.fsEndField)

        return myObjs


    security.declareProtected(ModifyPortalContent, 'setId')
    def setId(self, value):
        """Sets the object id. Changes both object and field id.
        """

        badIds = (
            'language',
            'form',
            'form_submit',
            'fieldset',
            'last_referer',
            'add_reference',
            )

        if value in badIds:
            raise BadRequest, 'The id "%s" is reserved.' % value

        ATFolder.setId(self, value)
        self.fsStartField.__name__ = self.getId()


    def manage_afterAdd(self, item, container):
        # XXX TODO: when we're done with 2.1.x, implement this via event subscription

        ATFolder.manage_afterAdd(self, item, container)

        id = self.getId()        
        if self.fsStartField.__name__ != id:
            self.fsStartField.__name__ = id


    # security is inherited
    def checkIdAvailable(self, id):
        """ Checks for good id by asking form folder """
        
        return self.formFolderObject().checkIdAvailable(id)


    def conditionalFieldDL(self):
        """ returns a display list contianing all fields within this form
        that can be used to evaluate the condition for this fieldset """
        fields = self.formFolderObject().objectValues('FormSelectionField')

        vocab = DisplayList()

        for f in fields:
            fieldvocab = f.fgField.Vocabulary(f)
            fieldvocab = '; '.join(fieldvocab.keys())
            vocab.add(f.getId(), '%s - %s' % (
                        f.Title(),
                        fieldvocab,
                        ))

        return vocab

registerATCT(FieldsetFolder, PROJECTNAME)

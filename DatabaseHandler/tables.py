from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import declarative_base

from sqlalchemy import (
    Column,
    Integer,
    String,
    Unicode,
    Boolean,
    DateTime,
    LargeBinary,
    ForeignKey,
    func,
    text
)

# Create a "Base" class that all table models will inherit from
Base = declarative_base()

def ro_time():
    return datetime.now(ZoneInfo("Europe/Bucharest")).replace(tzinfo=None)


class DescProduct(Base):
    """
    SQLAlchemy model for the Desc_Product table.
    """
    # The name of the actual table in the database
    __tablename__ = 'Desc_Product'

    # --- Column Definitions ---
    ProductID = Column(String(15), primary_key=True)
    ProductGroupCode = Column(String(10))
    GTIN = Column(String(14), unique=True)
    Description = Column(String(50), nullable=False)

    # For column names with spaces like [Vendor No], we define a valid
    # Python attribute (VendorNo) and pass the real column name as a string.
    VendorNo = Column('Vendor No', String(10))
    Name = Column(String(50), nullable=False)
    VendorItemNo = Column('Vendor Item No', String(10), nullable=False)
    TariffNo = Column('Tariff No', String(10), nullable=False)
    TariffName = Column('Tariff Name', String(50), nullable=False)

    CountryPurchasedCode = Column(String(10), nullable=False)
    CountryRegionOfOriginCode = Column(String(10), nullable=False)
    ManufacturerCode = Column(String(20), nullable=False)
    ManufacturerName = Column(String(50), nullable=False)
    DivisonCode = Column(String(1), nullable=False)
    DivisionName = Column(String(10), nullable=False)
    ItemCategoryCode = Column(String(50), nullable=False)
    ItemCategoryName = Column(String(50), nullable=False)
    ProductGroupName = Column(String(50), nullable=False)

    # BIT column with a default value of 0
    StatusDescription = Column(Boolean, server_default=text('0'))


class DescCategoryMapping(Base):
    """
    SQLAlchemy model for the Desc_CategoryMapping table.
    Maps a ProductGroupCode to a specific Category and Subcategory.
    """
    __tablename__ = 'Desc_CategoryMapping'

    MappingCategoryID = Column(Integer, primary_key=True)
    ProductGroupCode = Column(String(10), ForeignKey("Desc_Product.ProductGroupCode"), nullable=False)
    Category = Column(String(25), nullable=False)
    Subcategory = Column(String(25), nullable=False)
    

class DescDescription(Base):
    """
    SQLAlchemy model for the Desc_Description table.
    """
    __tablename__ = 'Desc_Description'

    DescriptionID = Column(Integer, primary_key=True)
    ProductID = Column(String(15), ForeignKey("Desc_Product.ProductID"), nullable=False)
    ProductName = Column(String(255))
    TextDescription = Column(LargeBinary)
    TimeStamp = Column(
        DateTime(timezone=True),
        nullable=False,
        # 'default': Sets the timestamp when a new record is CREATED.
        default=ro_time(),
        # 'onupdate': Sets the timestamp when a record is UPDATED.
        onupdate=ro_time()
    )
    Link = Column(String(255))

    def __repr__(self):
        """Optional: A helper method for clean printing."""
        return (
            f"<DescDescription(DescriptionID={self.DescriptionID}, "
            f"ProductID='{self.ProductID}')>"
        )
    
    def decode_description(self):
        try:
            # Use the appropriate encoding format
            binary_data = self.TextDescription
            text_string = binary_data.decode('utf-16')
            return text_string 
        except Exception as e:
            print(f"Could not decode binary data: {e}")


class DescSpecification(Base):
    """
    SQLAlchemy ORM model for the 'Desc_Specification' table.
    """
    __tablename__ = "Desc_Specification"

    SpecificationID = Column(Integer, primary_key=True)
    ProductID = Column(String(15), nullable=False)
    SpecificationAttribute = Column(Unicode(255), nullable=False)
    Value = Column(Unicode(50), nullable=False)
    TimeStamp = Column(
        DateTime(timezone=True),
        nullable=False,
        # 'default': Sets the timestamp when a new record is CREATED.
        default=ro_time(),
        # 'onupdate': Sets the timestamp when a record is UPDATED.
        onupdate=ro_time()
    )

    # An optional __repr__ method for clean printing of objects
    def __repr__(self):
        return (
            f"<DescSpecification(SpecificationID={self.SpecificationID}, "
            f"ProductID='{self.ProductID}', "
            f"Attribute='{self.SpecificationAttribute}', "
            f"Value='{self.Value}')>"
        )

import os
import urllib
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, Query, InstrumentedAttribute
from typing import List, Any, Literal
from DatabaseHandler.tables import DescProduct, DescDescription, DescCategoryMapping, DescSpecification

# Define the allowed search types for type hinting and validation
SearchType = Literal["exact", "contains", "starts_with", "ends_with"]


class DatabaseHandler():
    
    def __init__(self, credentials):
        self.credentials = credentials # de forma "UID=user;PWD=pass"
        self.session: Session =  self.create_session()
        print("Connection established with the database...", end='')

    # finished
    def create_session(self):

        connection_string = (
            f"{self.credentials};"
            f"driver={{ODBC Driver 17 for SQL Server}};"
            f"server=192.168.1.34;"
            f"database=APLICATII;"
        )
        quoted_conn_str = urllib.parse.quote_plus(connection_string)

        engine = create_engine(f"mssql+pyodbc:///?odbc_connect={quoted_conn_str}")

        Session = sessionmaker(bind=engine)
        return Session()

 # --- Funcție modificată: adaugă sau updatează descriere + nume produs ---
    def add_or_update_description(  
        self,
        product_id: str,
        product_name: str,
        description_text: str,
        link: str,
        encoding: str = 'utf-16'
    ):
        """
        Inserts or updates a product description and product name in the database.
        """
        try:
            # Encode description
            encoded_description = description_text.encode(encoding)
            
            # Caută descriere existentă
            existing_desc = self.session.query(DescDescription).filter_by(ProductID=product_id).first()

            if existing_desc:
                # UPDATE
                print(f"Updating description and name for ProductID: {product_id}")
                existing_desc.TextDescription = encoded_description
                existing_desc.ProductName = product_name
                existing_desc.Link = link
            else:
                # CREATE
                print(f"Creating new description for ProductID: {product_id}")
                new_desc = DescDescription(
                    ProductID=product_id,
                    ProductName=product_name,
                    TextDescription=encoded_description,
                    Link = link
                )
                self.session.add(new_desc)

            # update the status at the end in Desc_Product daca are desc
            try:
                if description_text != "Not found":
                    product = self.session.query(DescProduct).filter_by(ProductID=product_id).first()
                    product.StatusDescription = 1
            except:
                pass

            # Commit
            self.session.commit()
            print(f"Successfully committed description and name to the database for ProductID: {product_id}.")

        except Exception as e:
            print(f"Database error occurred: {e}")
            self.session.rollback()
            return None

    def add_or_update_specifications(
        self,
        product_id: str,
        specifications: dict[str, str]
    ):
        """
        Inserts or updates product specifications in the Desc_Specification table
        for the given ProductID.

        Args:
            product_id (str): ID-ul produsului.
            specifications (dict): Dicționar cu numele specificației ca cheie și valoarea ca string.
        """
        try:
            for spec_attr, spec_value in specifications.items():

                if isinstance(spec_value, dict):
                    print("cazul mega special in care prelucram dictioanr in dictionar ------------------------------------------------------")
                    print(specifications)
                    specifications |= spec_value
                    del specifications[spec_attr]
                    print(specifications)
                    self.add_or_update_specifications(product_id,specifications)
                    return 

                # Verifică dacă specificația există deja
                existing_spec = self.session.query(DescSpecification).filter_by(
                    ProductID=product_id,
                    SpecificationAttribute=spec_attr
                ).first()

                if existing_spec:
                    # UPDATE
                    # print(f"Updating specification '{spec_attr}' for ProductID: {product_id}")
                    existing_spec.Value = spec_value
                else:
                    # CREATE
                    # print(f"Creating specification '{spec_attr}' for ProductID: {product_id}")
                    new_spec = DescSpecification(
                        ProductID=product_id,
                        SpecificationAttribute=spec_attr,
                        Value=spec_value
                    )
                    self.session.add(new_spec)

            # Commit
            self.session.commit()
            print(f"✅ Successfully committed specifications for ProductID {product_id}.\n")

        except Exception as e:
            print(f"Database error occurred: {e}")
            self.session.rollback()
            return None

    # kinda finished, merge
    def search_table(
        self,
        model_class_attributes: List[InstrumentedAttribute],
        search_column: str,
        search_value: Any,
        search_type: SearchType = "exact"
    ) -> List[Any]:
        """
        Performs a flexible search on a given table (model).

        Args:
            session (Session): The active SQLAlchemy session.
            model_class_attributes (List[InstrumentedAttribute]): The SQLAlchemy attributes to query.
            search_column (str): The string name of the column to search in.
            search_value (Any): The value to search for.
            search_type (SearchType): The type of search to perform.
                - "exact": Finds an exact match (default).
                - "contains": Finds if the column contains the value (case-sensitive LIKE).
                - "starts_with": Finds if the column starts with the value.
                - "ends_with": Finds if the column ends with the value.

        Returns:
            A list of matching model objects, or an empty list if none are found or an error occurs.
        """
        try:
            column_attr = getattr(model_class_attributes[0].class_, search_column)

            match search_type:
                case "exact":
                    query = self.session.query(*model_class_attributes).filter(column_attr == search_value)
                case "contains":
                    query = self.session.query(*model_class_attributes).filter(column_attr.like(f"%{search_value}%"))
                case "starts_with":
                    query = self.session.query(*model_class_attributes).filter(column_attr.like(f"{search_value}%"))
                case "ends_with":
                    query = self.session.query(*model_class_attributes).filter(column_attr.like(f"%{search_value}"))
                case default:
                # This case should ideally not be reached due to the Literal type hint
                    print(f"Error: Invalid search_type '{search_type}'.")
                    return []

            return query.all()

        except AttributeError as e:
            print(f"Error: Column '{search_column}' does not exist on model '{model_class_attributes.__name__}'.")
            print (e)
            return []
        except Exception as e:
            print(f"An error occurred: {e}")
            self.session.rollback()
            return []

        """
        Category search
        """    
    def mapping_search(self, value:str)->tuple[str,str]:
        category: Query = self.search_table(
        model_class_attributes=[DescCategoryMapping.Category,DescCategoryMapping.Subcategory],
        search_column="ProductGroupCode",
        search_value=value,
        search_type="exact"
        )
        category = category.first()
        return (category)

    def get_items(self) -> dict[str,list]:
        
        products : List[DescProduct] = self.search_table(
            model_class_attributes=[DescProduct.ProductID, DescProduct.Description, DescProduct.ManufacturerName],
            search_column="StatusDescription",
            search_value=0,
            search_type="exact"
        )

        keys = ["product_id", "products", "manufacturers"]
        columns = zip(*products)
        columnar_dict = {key: list(column_values) for key, column_values in zip(keys, columns)}
        # for product, manufacturer in zip(columnar_dict["products"], columnar_dict["manufacturers"]):
        #     print(product, manufacturer)
        return columnar_dict

# db_handler = DatabaseHandlerr()

# db_handler.get_items()

# products = db_handler.search_table(
#     model_class=DescProduct,
#     search_column="ProductID",
#     search_value="G",
#     search_type="starts_with"
# )
# for p in products:
#     print(f"  -> Found: {p.Name}  {p.Description}  {p.TariffName}")


    # --- EXAMPLE 1: Find a single product by its primary key ---
"""print("Finding product with ID 'PROD-001'...")
    product = session.query(DescProduct).filter_by(ProductID='G00000000001591').first()

    # The result is an object of your DescProduct class
    if product:
        print(f"  -> Found Product: {product.Name}")
        print(f"  -> Manufacturer: {product.ManufacturerName}")
        # Access columns with spaces using their Python attribute names
        print(f"  -> Vendor Number: {product.VendorNo}")
    """

    # --- EXAMPLE 2: Find all products with a specific name ---
"""print("\nFinding all products named 'Widget'...")
    widgets = session.query(DescProduct).filter(DescProduct.Name == 'Widget').all()

    print(f"  -> Found {len(widgets)} widgets.")
    for widget in widgets:
        # The __repr__ method we defined gets called here for clean printing
        print(f"  - {widget}")"""
    
    # Update the description table
    # add_or_update_description("P12d33f5","test")

    # EXAMPLE 3: Various search modes
# print("Searching for products...")
# products = db_handler.search_table(
#     model_class=DescProduct,
#     search_column="TariffName",
#     search_value="Altele",
#     search_type="exact"
# )
# for p in products:                                                
#     print(f"  -> Found: {p.Name}  {p.Description}  {p.TariffName}")

    # product = session.query(DescDescription).filter_by(ProductID='P123').first()
    # if product:
    #     print(f"  -> Found Product description: {bin(product.TextDescription)}")
    # # print(product)


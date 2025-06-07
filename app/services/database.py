import sqlalchemy
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, ForeignKey, DateTime, Numeric
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URI)


def setup_database():
    """Create tables and seed Chinook-like data if not present."""
    try:

        with engine.connect() as connection:
            try:
                connection.execute(text("SELECT 1 FROM Artist LIMIT 1"))
                logger.info("Database tables already exist")
                return
            except sqlalchemy.exc.OperationalError:
                logger.info(
                    "Database tables not found. Creating Chinook-like schema...")
                _create_chinook_schema(connection)
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        raise


def _create_chinook_schema(connection):
    """Create Chinook-like database schema with comprehensive sample data"""
    try:

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS Artist (
                ArtistId INTEGER PRIMARY KEY,
                Name NVARCHAR(120)
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS Album (
                AlbumId INTEGER PRIMARY KEY,
                Title NVARCHAR(160) NOT NULL,
                ArtistId INTEGER NOT NULL,
                FOREIGN KEY (ArtistId) REFERENCES Artist (ArtistId)
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS Genre (
                GenreId INTEGER PRIMARY KEY,
                Name NVARCHAR(120)
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS MediaType (
                MediaTypeId INTEGER PRIMARY KEY,
                Name NVARCHAR(120)
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS Track (
                TrackId INTEGER PRIMARY KEY,
                Name NVARCHAR(200) NOT NULL,
                AlbumId INTEGER,
                MediaTypeId INTEGER,
                GenreId INTEGER,
                Composer NVARCHAR(220),
                Milliseconds INTEGER,
                Bytes INTEGER,
                UnitPrice NUMERIC(10,2),
                FOREIGN KEY (AlbumId) REFERENCES Album (AlbumId),
                FOREIGN KEY (MediaTypeId) REFERENCES MediaType (MediaTypeId),
                FOREIGN KEY (GenreId) REFERENCES Genre (GenreId)
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS Customer (
                CustomerId INTEGER PRIMARY KEY,
                FirstName NVARCHAR(40) NOT NULL,
                LastName NVARCHAR(20) NOT NULL,
                Company NVARCHAR(80),
                Address NVARCHAR(70),
                City NVARCHAR(40),
                State NVARCHAR(40),
                Country NVARCHAR(40),
                PostalCode NVARCHAR(10),
                Phone NVARCHAR(24),
                Fax NVARCHAR(24),
                Email NVARCHAR(60) NOT NULL,
                SupportRepId INTEGER
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS Employee (
                EmployeeId INTEGER PRIMARY KEY,
                LastName NVARCHAR(20) NOT NULL,
                FirstName NVARCHAR(20) NOT NULL,
                Title NVARCHAR(30),
                ReportsTo INTEGER,
                BirthDate DATETIME,
                HireDate DATETIME,
                Address NVARCHAR(70),
                City NVARCHAR(40),
                State NVARCHAR(40),
                Country NVARCHAR(40),
                PostalCode NVARCHAR(10),
                Phone NVARCHAR(24),
                Fax NVARCHAR(24),
                Email NVARCHAR(60)
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS Invoice (
                InvoiceId INTEGER PRIMARY KEY,
                CustomerId INTEGER NOT NULL,
                InvoiceDate DATETIME NOT NULL,
                BillingAddress NVARCHAR(70),
                BillingCity NVARCHAR(40),
                BillingState NVARCHAR(40),
                BillingCountry NVARCHAR(40),
                BillingPostalCode NVARCHAR(10),
                Total NUMERIC(10,2) NOT NULL,
                FOREIGN KEY (CustomerId) REFERENCES Customer (CustomerId)
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS InvoiceLine (
                InvoiceLineId INTEGER PRIMARY KEY,
                InvoiceId INTEGER NOT NULL,
                TrackId INTEGER NOT NULL,
                UnitPrice NUMERIC(10,2) NOT NULL,
                Quantity INTEGER NOT NULL,
                FOREIGN KEY (InvoiceId) REFERENCES Invoice (InvoiceId),
                FOREIGN KEY (TrackId) REFERENCES Track (TrackId)
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS Playlist (
                PlaylistId INTEGER PRIMARY KEY,
                Name NVARCHAR(120)
            )
        """))

        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS PlaylistTrack (
                PlaylistId INTEGER NOT NULL,
                TrackId INTEGER NOT NULL,
                PRIMARY KEY (PlaylistId, TrackId),
                FOREIGN KEY (PlaylistId) REFERENCES Playlist (PlaylistId),
                FOREIGN KEY (TrackId) REFERENCES Track (TrackId)
            )
        """))

        _insert_sample_data(connection)

        connection.commit()
        logger.info("Chinook-like database created and seeded successfully")

    except Exception as e:
        logger.error(f"Error creating Chinook schema: {e}")
        connection.rollback()
        raise


def _insert_sample_data(connection):
    """Insert comprehensive sample data"""

    artists_data = [
        (1, 'AC/DC'),
        (2, 'Accept'),
        (3, 'Aerosmith'),
        (4, 'Alanis Morissette'),
        (5, 'Alice In Chains'),
        (6, 'Antônio Carlos Jobim'),
        (7, 'Apocalyptica'),
        (8, 'Audioslave'),
        (9, 'BackBeat'),
        (10, 'The Beatles'),
        (11, 'Billy Cobham'),
        (12, 'Black Label Society'),
        (13, 'Black Sabbath'),
        (14, 'Body Count'),
        (15, 'Bruce Dickinson')
    ]

    for artist_id, name in artists_data:
        connection.execute(text(
            "INSERT OR IGNORE INTO Artist (ArtistId, Name) VALUES (:id, :name)"
        ), {"id": artist_id, "name": name})

    genres_data = [
        (1, 'Rock'),
        (2, 'Jazz'),
        (3, 'Metal'),
        (4, 'Alternative & Punk'),
        (5, 'Classical'),
        (6, 'Blues'),
        (7, 'Latin'),
        (8, 'Reggae'),
        (9, 'Pop'),
        (10, 'Soundtrack')
    ]

    for genre_id, name in genres_data:
        connection.execute(text(
            "INSERT OR IGNORE INTO Genre (GenreId, Name) VALUES (:id, :name)"
        ), {"id": genre_id, "name": name})

    media_types_data = [
        (1, 'MPEG audio file'),
        (2, 'Protected AAC audio file'),
        (3, 'Protected MPEG-4 video file'),
        (4, 'Purchased AAC audio file'),
        (5, 'AAC audio file')
    ]

    for media_id, name in media_types_data:
        connection.execute(text(
            "INSERT OR IGNORE INTO MediaType (MediaTypeId, Name) VALUES (:id, :name)"
        ), {"id": media_id, "name": name})

    albums_data = [
        (1, 'For Those About To Rock We Salute You', 1),
        (2, 'Balls to the Wall', 2),
        (3, 'Restless and Wild', 2),
        (4, 'Let There Be Rock', 1),
        (5, 'Big Ones', 3),
        (6, 'Jagged Little Pill', 4),
        (7, 'Facelift', 5),
        (8, 'Warner 25 Anos', 6),
        (9, 'Plays Metallica By Four Cellos', 7),
        (10, 'Audioslave', 8),
        (11, 'Abbey Road', 10),
        (12, 'Let It Be', 10),
        (13, 'Paranoid', 13),
        (14, 'The Chemical Wedding', 15),
        (15, 'Mafia', 12)
    ]

    for album_id, title, artist_id in albums_data:
        connection.execute(text(
            "INSERT OR IGNORE INTO Album (AlbumId, Title, ArtistId) VALUES (:id, :title, :artist_id)"
        ), {"id": album_id, "title": title, "artist_id": artist_id})

    tracks_data = [
        (1, 'For Those About To Rock (We Salute You)', 1, 1, 1,
         'Angus Young, Malcolm Young, Brian Johnson', 343719, 11170334, 0.99),
        (2, 'Balls to the Wall', 2, 1, 1, None, 342562, 5510424, 0.99),
        (3, 'Fast As a Shark', 3, 1, 1,
         'F. Baltes, S. Kaufman, U. Dirkscneider & W. Hoffman', 230619, 3990994, 0.99),
        (4, 'Restless and Wild', 3, 1, 1,
         'F. Baltes, R.A. Smith-Diesel, S. Kaufman, U. Dirkscneider & W. Hoffman', 252051, 4331779, 0.99),
        (5, 'Princess of the Dawn', 3, 1, 1,
         'Deaffy & R.A. Smith-Diesel', 375418, 6290521, 0.99),
        (6, 'Put The Finger On You', 1, 1, 1,
         'Angus Young, Malcolm Young, Brian Johnson', 205662, 6713451, 0.99),
        (7, 'Let There Be Rock', 4, 1, 1,
         'Angus Young, Malcolm Young, Bon Scott', 366654, 12021261, 0.99),
        (8, 'Inject The Venom', 1, 1, 1,
         'Angus Young, Malcolm Young, Brian Johnson', 210834, 6852860, 0.99),
        (9, 'Dream On', 5, 1, 1, 'Steven Tyler', 294321, 9556134, 0.99),
        (10, 'Crazy', 5, 1, 1, 'Steven Tyler, Joe Perry, Desmond Child',
         316656, 10402398, 0.99),
        (11, 'You Oughta Know', 6, 1, 4,
         'Alanis Morissette, Glen Ballard', 249391, 8196916, 0.99),
        (12, 'Ironic', 6, 1, 4, 'Alanis Morissette, Glen Ballard', 229825, 7598866, 0.99),
        (13, 'Man In The Box', 7, 1, 4,
         'Jerry Cantrell, Layne Staley', 286641, 9310272, 0.99),
        (14, 'Would?', 7, 1, 4, 'Jerry Cantrell', 207081, 6747993, 0.99),
        (15, 'Come As You Are', 8, 1, 1,
         'Chris Cornell, Tom Morello, Tim Commerford, Brad Wilk', 279840, 9158611, 0.99),
        (16, 'Like a Stone', 10, 1, 1,
         'Chris Cornell, Tom Morello, Tim Commerford, Brad Wilk', 294034, 9626390, 0.99),
        (17, 'Come Together', 11, 1, 1,
         'John Lennon, Paul McCartney', 259721, 8490528, 0.99),
        (18, 'Something', 11, 1, 1, 'George Harrison', 182956, 5990473, 0.99),
        (19, 'Let It Be', 12, 1, 1, 'John Lennon, Paul McCartney', 243026, 7946148, 0.99),
        (20, 'The Long and Winding Road', 12, 1, 1,
         'John Lennon, Paul McCartney', 217986, 7131238, 0.99),
        (21, 'Paranoid', 13, 1, 3,
         'Tony Iommi, Geezer Butler, Ozzy Osbourne, Bill Ward', 170280, 5566931, 0.99),
        (22, 'Iron Man', 13, 1, 3,
         'Tony Iommi, Geezer Butler, Ozzy Osbourne, Bill Ward', 356462, 11673176, 0.99),
        (23, 'The Chemical Wedding', 14, 1, 3,
         'Bruce Dickinson, Roy Z', 245213, 8029687, 0.99),
        (24, 'King In Crimson', 14, 1, 3,
         'Bruce Dickinson, Roy Z', 260000, 8512000, 0.99),
        (25, 'Fire It Up', 15, 1, 3, 'Zakk Wylde', 314573, 10303390, 0.99)
    ]

    for track_data in tracks_data:
        connection.execute(text("""
            INSERT OR IGNORE INTO Track
            (TrackId, Name, AlbumId, MediaTypeId, GenreId,
             Composer, Milliseconds, Bytes, UnitPrice)
            VALUES (:track_id, :name, :album_id, :media_type_id, :genre_id, :composer, :milliseconds, :bytes, :unit_price)
        """), {
            "track_id": track_data[0],
            "name": track_data[1],
            "album_id": track_data[2],
            "media_type_id": track_data[3],
            "genre_id": track_data[4],
            "composer": track_data[5],
            "milliseconds": track_data[6],
            "bytes": track_data[7],
            "unit_price": track_data[8]
        })

    employees_data = [
        (1, 'Adams', 'Andrew', 'General Manager', None, '1962-02-18 00:00:00', '2002-08-14 00:00:00',
         '11120 Jasper Ave NW', 'Edmonton', 'AB', 'Canada', 'T5K 2N1', '+1 (780) 428-9482', '+1 (780) 428-3457', 'andrew@chinookcorp.com'),
        (2, 'Edwards', 'Nancy', 'Sales Manager', 1, '1958-12-08 00:00:00', '2002-05-01 00:00:00',
         '825 8 Ave SW', 'Calgary', 'AB', 'Canada', 'T2P 2T3', '+1 (403) 262-3443', '+1 (403) 262-3322', 'nancy@chinookcorp.com'),
        (3, 'Peacock', 'Jane', 'Sales Support Agent', 2, '1973-08-29 00:00:00', '2002-04-01 00:00:00',
         '1111 6 Ave SW', 'Calgary', 'AB', 'Canada', 'T2P 5M5', '+1 (403) 262-3443', '+1 (403) 262-6712', 'jane@chinookcorp.com'),
        (4, 'Park', 'Margaret', 'Sales Support Agent', 2, '1947-09-19 00:00:00', '2003-05-03 00:00:00',
         '683 10 Street SW', 'Calgary', 'AB', 'Canada', 'T2P 5G3', '+1 (403) 263-4423', '+1 (403) 263-4289', 'margaret@chinookcorp.com'),
        (5, 'Johnson', 'Steve', 'Sales Support Agent', 2, '1965-03-03 00:00:00', '2003-10-17 00:00:00',
         '7727B 41 Ave', 'Calgary', 'AB', 'Canada', 'T3B 1Y7', '1 (780) 836-9987', '1 (780) 836-9543', 'steve@chinookcorp.com'),
        (6, 'Mitchell', 'Michael', 'IT Manager', 1, '1973-07-01 00:00:00', '2003-10-17 00:00:00',
         '5827 Bowness Road NW', 'Calgary', 'AB', 'Canada', 'T3B 0C5', '+1 (403) 246-9887', '+1 (403) 246-9899', 'michael@chinookcorp.com'),
        (7, 'King', 'Robert', 'IT Staff', 6, '1970-05-29 00:00:00', '2004-01-02 00:00:00',
         '590 Columbia Boulevard West', 'Lethbridge', 'AB', 'Canada', 'T1K 5N8', '+1 (403) 456-9986', '+1 (403) 456-8485', 'robert@chinookcorp.com'),
        (8, 'Callahan', 'Laura', 'IT Staff', 6, '1968-01-09 00:00:00', '2004-03-04 00:00:00',
         '923 7 ST NW', 'Lethbridge', 'AB', 'Canada', 'T1H 1Y8', '+1 (403) 467-3351', '+1 (403) 467-8772', 'laura@chinookcorp.com')
    ]

    for emp_data in employees_data:
        connection.execute(text("""
            INSERT OR IGNORE INTO Employee
            (EmployeeId, LastName, FirstName, Title, ReportsTo, BirthDate,
             HireDate, Address, City, State, Country, PostalCode, Phone, Fax, Email)
            VALUES (:emp_id, :last_name, :first_name, :title, :reports_to, :birth_date, :hire_date, :address, :city, :state, :country, :postal_code, :phone, :fax, :email)
        """), {
            "emp_id": emp_data[0], "last_name": emp_data[1], "first_name": emp_data[2], "title": emp_data[3],
            "reports_to": emp_data[4], "birth_date": emp_data[5], "hire_date": emp_data[6], "address": emp_data[7],
            "city": emp_data[8], "state": emp_data[9], "country": emp_data[10], "postal_code": emp_data[11],
            "phone": emp_data[12], "fax": emp_data[13], "email": emp_data[14]
        })

    customers_data = [
        (1, 'Luís', 'Gonçalves', 'Embraer - Empresa Brasileira de Aeronáutica S.A.', 'Av. Brigadeiro Faria Lima, 2170',
         'São José dos Campos', 'SP', 'Brazil', '12227-000', '+55 (12) 3923-5555', '+55 (12) 3923-5566', 'luisg@embraer.com.br', 3),
        (2, 'Leonie', 'Köhler', None, 'Theodor-Heuss-Straße 34', 'Stuttgart', None,
         'Germany', '70174', '+49 0711 2842222', None, 'leonekohler@surfeu.de', 5),
        (3, 'François', 'Tremblay', None, '1498 rue Bélanger', 'Montréal', 'QC',
         'Canada', 'H2G 1A7', '+1 (514) 721-4711', None, 'ftremblay@gmail.com', 3),
        (4, 'Bjørn', 'Hansen', None, 'Ullevålsveien 14', 'Oslo', None,
         'Norway', '0171', '+47 22 44 22 22', None, 'bjorn.hansen@yahoo.no', 4),
        (5, 'František', 'Wichterlová', 'JetBrains s.r.o.', 'Klanova 9/506', 'Prague', None,
         'Czech Republic', '14700', '+420 2 4172 5555', '+420 2 4172 5555', 'frantisekw@jetbrains.com', 4),
        (6, 'Helena', 'Holý', None, 'Rilská 3174/6', 'Prague', None,
         'Czech Republic', '14300', '+420 2 4177 0449', None, 'hholy@gmail.com', 5),
        (7, 'Astrid', 'Gruber', None, 'Rotenturmstraße 4, 1010 Innere Stadt', 'Vienne',
         None, 'Austria', '1010', '+43 01 5134505', None, 'astrid.gruber@apple.at', 5),
        (8, 'Daan', 'Peeters', None, 'Grétrystraat 63', 'Brussels', None,
         'Belgium', '1000', '+32 02 219 03 03', None, 'daan_peeters@apple.be', 4),
        (9, 'Kara', 'Nielsen', None, 'Sønder Boulevard 51', 'Copenhagen', None,
         'Denmark', '1720', '+453 3331 9991', None, 'kara.nielsen@jubii.dk', 4),
        (10, 'Eduardo', 'Martins', 'Woodstock Discos', 'Rua Dr. Falcão Filho, 155', 'São Paulo', 'SP',
         'Brazil', '01007-010', '+55 (11) 3033-5446', '+55 (11) 3033-4564', 'eduardo@woodstock.com.br', 4),
        (11, 'Alexandre', 'Rocha', 'Banco do Brasil S.A.', 'Av. Paulista, 2022', 'São Paulo', 'SP',
         'Brazil', '01310-200', '+55 (11) 3055-3278', '+55 (11) 3055-8131', 'alero@uol.com.br', 5),
        (12, 'Roberto', 'Almeida', 'Riotur', 'Praça Pio X, 119', 'Rio de Janeiro', 'RJ', 'Brazil',
         '20040-020', '+55 (21) 2271-7000', '+55 (21) 2271-7070', 'roberto.almeida@riotur.gov.br', 3),
        (13, 'Fernanda', 'Ramos', None, 'Qe 7 Bloco G', 'Brasília', 'DF', 'Brazil', '71020-677',
         '+55 (61) 3363-5547', '+55 (61) 3363-7855', 'fernadaramos4@uol.com.br', 4),
        (14, 'Mark', 'Philips', 'Telus', '8210 111 ST NW', 'Edmonton', 'AB', 'Canada',
         'T6G 2C7', '+1 (780) 434-4554', '+1 (780) 434-5565', 'mphilips12@shaw.ca', 5),
        (15, 'Jennifer', 'Peterson', 'Rogers Canada', '700 W Pender Street', 'Vancouver', 'BC',
         'Canada', 'V6C 1G8', '+1 (604) 688-2255', '+1 (604) 688-8756', 'jenniferp@rogers.ca', 3),
        (16, 'Frank', 'Harris', 'Google Inc.', '1600 Amphitheatre Pkwy', 'Mountain View', 'CA',
         'USA', '94043-1351', '+1 (650) 253-0000', '+1 (650) 253-0000', 'fharris@google.com', 4),
        (17, 'Jack', 'Smith', 'Microsoft Corporation', '1 Microsoft Way', 'Redmond', 'WA', 'USA',
         '98052-8300', '+1 (425) 882-8080', '+1 (425) 882-8081', 'jacksmith@microsoft.com', 5),
        (18, 'Michelle', 'Brooks', None, '627 Broadway', 'New York', 'NY', 'USA',
         '10012-2612', '+1 (212) 221-3546', '+1 (212) 221-4679', 'michelleb@aol.com', 3),
        (19, 'Tim', 'Goyer', 'Apple Inc.', '1 Infinite Loop', 'Cupertino', 'CA', 'USA',
         '95014', '+1 (408) 996-1010', '+1 (408) 996-1011', 'tgoyer@apple.com', 3),
        (20, 'Dan', 'Miller', None, '541 Del Medio Avenue', 'Mountain View', 'CA',
         'USA', '94040-111', '+1 (650) 644-3358', None, 'dmiller@comcast.com', 4)
    ]

    for cust_data in customers_data:
        connection.execute(text("""
            INSERT OR IGNORE INTO Customer
            (CustomerId, FirstName, LastName, Company, Address, City,
             State, Country, PostalCode, Phone, Fax, Email, SupportRepId)
            VALUES (:cust_id, :first_name, :last_name, :company, :address, :city, :state, :country, :postal_code, :phone, :fax, :email, :support_rep_id)
        """), {
            "cust_id": cust_data[0], "first_name": cust_data[1], "last_name": cust_data[2], "company": cust_data[3],
            "address": cust_data[4], "city": cust_data[5], "state": cust_data[6], "country": cust_data[7],
            "postal_code": cust_data[8], "phone": cust_data[9], "fax": cust_data[10], "email": cust_data[11], "support_rep_id": cust_data[12]
        })

    invoices_data = [
        (1, 2, '2021-01-01 00:00:00', 'Theodor-Heuss-Straße 34',
         'Stuttgart', None, 'Germany', '70174', 1.98),
        (2, 4, '2021-01-02 00:00:00', 'Ullevålsveien 14',
         'Oslo', None, 'Norway', '0171', 3.96),
        (3, 8, '2021-01-03 00:00:00', 'Grétrystraat 63',
         'Brussels', None, 'Belgium', '1000', 5.94),
        (4, 14, '2021-01-06 00:00:00', '8210 111 ST NW',
         'Edmonton', 'AB', 'Canada', 'T6G 2C7', 8.91),
        (5, 23, '2021-01-11 00:00:00', '69 Salem Street',
         'Boston', 'MA', 'USA', '2113', 13.86),
        (6, 37, '2021-01-19 00:00:00', 'Berger Straße 10',
         'Frankfurt', None, 'Germany', '60316', 0.99),
        (7, 38, '2021-02-01 00:00:00', 'Barbarossastraße 19',
         'Berlin', None, 'Germany', '10779', 1.98),
        (8, 40, '2021-02-01 00:00:00', '8, Rue Hanovre',
         'Paris', None, 'France', '75002', 1.98),
        (9, 42, '2021-02-02 00:00:00', '9, Place Louis Barthou',
         'Bordeaux', None, 'France', '33000', 3.96),
        (10, 46, '2021-02-03 00:00:00', '3 Chatham Street',
         'Dublin', 'Dublin', 'Ireland', None, 5.94),
        (11, 52, '2021-02-06 00:00:00', '202 Hoxton Street',
         'London', None, 'United Kingdom', 'N1 5LH', 8.91),
        (12, 2, '2021-02-11 00:00:00', 'Theodor-Heuss-Straße 34',
         'Stuttgart', None, 'Germany', '70174', 13.86),
        (13, 16, '2021-02-19 00:00:00', '1600 Amphitheatre Pkwy',
         'Mountain View', 'CA', 'USA', '94043-1351', 0.99),
        (14, 17, '2021-03-04 00:00:00', '1 Microsoft Way',
         'Redmond', 'WA', 'USA', '98052-8300', 1.98),
        (15, 19, '2021-03-04 00:00:00', '1 Infinite Loop',
         'Cupertino', 'CA', 'USA', '95014', 1.98)
    ]

    for inv_data in invoices_data:
        connection.execute(text("""
            INSERT OR IGNORE INTO Invoice
            (InvoiceId, CustomerId, InvoiceDate, BillingAddress, BillingCity,
             BillingState, BillingCountry, BillingPostalCode, Total)
            VALUES (:inv_id, :cust_id, :inv_date, :bill_addr, :bill_city, :bill_state, :bill_country, :bill_postal, :total)
        """), {
            "inv_id": inv_data[0], "cust_id": inv_data[1], "inv_date": inv_data[2], "bill_addr": inv_data[3],
            "bill_city": inv_data[4], "bill_state": inv_data[5], "bill_country": inv_data[6],
            "bill_postal": inv_data[7], "total": inv_data[8]
        })

    invoice_lines_data = [
        (1, 1, 2, 0.99, 1),
        (2, 1, 4, 0.99, 1),
        (3, 2, 6, 0.99, 1),
        (4, 2, 8, 0.99, 1),
        (5, 2, 10, 0.99, 1),
        (6, 2, 12, 0.99, 1),
        (7, 3, 16, 0.99, 1),
        (8, 3, 20, 0.99, 1),
        (9, 3, 24, 0.99, 1),
        (10, 3, 1, 0.99, 1),
        (11, 3, 3, 0.99, 1),
        (12, 3, 5, 0.99, 1),
        (13, 4, 7, 0.99, 1),
        (14, 4, 9, 0.99, 1),
        (15, 4, 11, 0.99, 1)
    ]

    for line_data in invoice_lines_data:
        connection.execute(text("""
            INSERT OR IGNORE INTO InvoiceLine
            (InvoiceLineId, InvoiceId, TrackId, UnitPrice, Quantity)
            VALUES (:line_id, :inv_id, :track_id, :unit_price, :quantity)
        """), {
            "line_id": line_data[0], "inv_id": line_data[1], "track_id": line_data[2],
            "unit_price": line_data[3], "quantity": line_data[4]
        })

    playlists_data = [
        (1, 'Music'),
        (2, 'Movies'),
        (3, 'TV Shows'),
        (4, 'Audiobooks'),
        (5, '90\'s Music'),
        (6, 'Audiobooks'),
        (7, 'Movies'),
        (8, 'Music'),
        (9, 'Music Videos'),
        (10, 'TV Shows'),
        (11, 'Brazilian Music'),
        (12, 'Classical'),
        (13, 'Classical 101 - Deep Cuts'),
        (14, 'Classical 101 - Next Steps'),
        (15, 'Classical 101 - The Basics')
    ]
    for playlist_data in playlists_data:
        connection.execute(text(
            "INSERT OR IGNORE INTO Playlist (PlaylistId, Name) VALUES (:id, :name)"
        ), {"id": playlist_data[0], "name": playlist_data[1]})

    playlist_tracks_data = [
        (1, 3402), (1, 3389), (1, 3390), (1, 3391), (1, 3392),
        (2, 3403), (2, 3404), (2, 3405), (2, 3406), (2, 3407),
        (3, 1), (3, 2), (3, 3), (3, 4), (3, 5),
        (4, 6), (4, 7), (4, 8), (4, 9), (4, 10),
        (5, 11), (5, 12), (5, 13), (5, 14), (5, 15)
    ]

    for pt_data in playlist_tracks_data:
        connection.execute(text(
            "INSERT OR IGNORE INTO PlaylistTrack (PlaylistId, TrackId) VALUES (:playlist_id, :track_id)"
        ), {"playlist_id": pt_data[0], "track_id": pt_data[1]})


def get_db_connection():
    """Return a LangChain SQLDatabase connection."""
    from langchain_community.utilities import SQLDatabase
    return SQLDatabase(engine=engine)


def get_table_info():
    """Get information about database tables"""
    try:
        with engine.connect() as connection:

            tables_result = connection.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """))
            tables = [row[0] for row in tables_result]

            schema_info = {}
            for table in tables:
                schema_result = connection.execute(
                    text(f"PRAGMA table_info({table})"))
                columns = []
                for row in schema_result:
                    columns.append({
                        "name": row[1],
                        "type": row[2],
                        "nullable": not row[3],
                        "primary_key": bool(row[5])
                    })
                schema_info[table] = columns

            return {
                "tables": tables,
                "schema": schema_info
            }
    except Exception as e:
        logger.error(f"Error getting table info: {e}")
        return {"tables": [], "schema": {}}

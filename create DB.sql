CREATE TABLE `details` (
  `SN` int NOT NULL AUTO_INCREMENT,
  `CIN` varchar(150) DEFAULT NULL,
  `Company` varchar(500) DEFAULT NULL,
  `ROC` varchar(150) DEFAULT NULL,
  `Status` varchar(150) DEFAULT NULL,
  `Url` varchar(500) NOT NULL,
  PRIMARY KEY (`SN`),
  UNIQUE KEY `Url` (`Url`)
);

CREATE TABLE `full_details` (
   `SN` int NOT NULL,
   `CIN` varchar(150) DEFAULT NULL,
   `LLP_Identification_Number` varchar(150) DEFAULT NULL,
   `Company_Name` varchar(500) DEFAULT NULL,
   `Company_Status` varchar(150) DEFAULT NULL,
   `ROC` varchar(150) DEFAULT NULL,
   `Registration_Number` varchar(20) DEFAULT NULL,
   `Company_Category` varchar(300) DEFAULT NULL,
   `Company_Sub_Category` varchar(200) DEFAULT NULL,
   `Class_of_Company` varchar(200) DEFAULT NULL,
   `Date_of_Incorporation` varchar(30) DEFAULT NULL,
   `Age_of_Company` varchar(30) DEFAULT NULL,
   `Activity` varchar(778) DEFAULT NULL,
   `Number_of_Members` varchar(20) DEFAULT NULL,
   `Authorised_Capital` varchar(20) DEFAULT NULL,
   `Paid_up_capital` varchar(20) DEFAULT NULL,
   `Listing_status` varchar(500) DEFAULT NULL,
   `Date_of_Last_Annual_General_Meeting` varchar(30) DEFAULT NULL,
   `Date_of_Latest_Balance_Sheet` varchar(30) DEFAULT NULL,
   `Email_ID` varchar(100) DEFAULT NULL,
   `Address` varchar(700) DEFAULT NULL,
   `Url` varchar(500) DEFAULT NULL,
   `Date_of_last_financial_year_end_date_for_which_Annual_R_f1e09135` varchar(700) DEFAULT NULL,
   `Date_of_last_financial_year_end_date_for_which_Statemen_d6a6f160` varchar(700) DEFAULT NULL,
   `Description_of_main_division` varchar(700) DEFAULT NULL,
   `Main_division_of_business_activity_to_be_carried_out_in_India` varchar(700) DEFAULT NULL,
   `Number_Of_Partners` varchar(700) DEFAULT NULL,
   `Number_of_Designated_Partners` varchar(700) DEFAULT NULL,
   `Total_Obligation_of_Contribution` varchar(700) DEFAULT NULL,
   `Country_of_Incorporation` varchar(700) DEFAULT NULL,
   `Foreign_Company_Registration_Number` varchar(700) DEFAULT NULL,
   `Type_Of_Office` varchar(700) DEFAULT NULL,
   `As_on` varchar(30) DEFAULT NULL,
   PRIMARY KEY (`SN`)
 );
 
 CREATE TABLE `director` (
  `SN` int NOT NULL,
  `DIN` varchar(50) NOT NULL,
  `Director_Name` varchar(82) DEFAULT NULL,
  `Designation` varchar(200) DEFAULT NULL,
  `Appointment_Date` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`SN`,`DIN`),
  UNIQUE KEY `SN` (`SN`,`DIN`)
);

 CREATE TABLE `shorted` (
  `Original` varchar(500) NOT NULL,
  `Edited` varchar(70) DEFAULT NULL,
  PRIMARY KEY (`Original`),
  UNIQUE KEY `Original` (`Original`),
  UNIQUE KEY `Edited` (`Edited`)
);

 
 
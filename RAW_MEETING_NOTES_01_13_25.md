# Meeting Notes from 01/13/2025 meeting with Lauri & Heide

## App Notes
### Investigate bug where Proposal PPTs do not show updated pricing when user changes prices on app
### In Tab 3, if user selected Option B, prices should be imported from proposal, rather than master.
### Future: Need option to create an entirely custom product
### Under Kitting Costs, need to show whether it's a cost per unit or for the order wholistically.
### Need to organize notes into 3 categories: Internal notes, client notes, and partner notes
### Add column for product type (flavor, color, etc) and update app logic. User has to be able to select.


## Other Notes

### 'Contact Us' form from website creates complications - PBP execs need to be able to fill in part of client setup / order forms
### Need different forms for New v. Existing "clients/potential clients" - Interest form v. Client form v. Fufillment form
### Need to clean up descriptions - Client facing v. bookkeeping v. internal descriptions
### Need to create a new Spreadsheet with Standard Markup logic; standard markups for each client

## Progress
### Changed schema from Country of Origin to disaggregated "Country of Origin (Made In)" and "Country of Origin (Ships From)" AND updated app to reflect new schema.
### Changed Client Max Price to a Budget Range
###  In Tab 3 Option B; made note of WHICH proposal is being loaded / which proposal we could import from
### Changed MOQ schema to disaggregated version (MOQ, MOV by Partner, PBP) in both spreadsheet and app.
### FIXED MAJOR BUG: App goes into a loading loop when trying to Remove items from Order in Tab 3
### For Customization Add-Ons, specified PBP Cost v. Client Prices. 
### Made schema-update subagent (call with e.g. "/schema-update rename 'MSRP' to 'Vendor Published MSRP'")




# Virginia ZIP Code Region Assignment

This file explains how to assign Virginia ZIP codes to common regions such as Northern Virginia, Richmond, Tidewater, and others.

## Common Virginia regions

The most frequently used Virginia regions include:

- Northern Virginia (NoVA)
- Richmond Metro
- Hampton Roads / Tidewater
- Charlottesville / Central Virginia
- Roanoke / Southwest Virginia
- Shenandoah Valley
- Southwest Virginia / Bristol
- Eastern Shore

## Approach to assigning ZIP codes to regions

Because ZIP codes do not follow strict political or geographic boundaries, the best approach is to assign regions by county or metro area and then map ZIP codes to those counties.

### Steps

1. Choose region definitions based on counties or metropolitan areas.
2. Use an official ZIP code–county crosswalk or a ZIP-to-county dataset.
3. Assign each ZIP code to the region containing its primary county.
4. For ZIP codes spanning multiple counties, choose the county with the highest population or the one most commonly associated with the ZIP.

## Example region definitions

### Northern Virginia
Counties and cities commonly included:
- Arlington County
- Fairfax County
- Loudoun County
- Prince William County
- Alexandria
- Falls Church
- Fairfax City
- Manassas / Manassas Park

### Richmond Metro
Counties and cities commonly included:
- Richmond City
- Chesterfield County
- Henrico County
- Hanover County
- Colonial Heights
- Petersburg
- Mechanicsville

### Hampton Roads / Tidewater
Counties and cities commonly included:
- Norfolk
- Virginia Beach
- Chesapeake
- Newport News
- Hampton
- Suffolk
- Portsmouth
- Williamsburg
- Gloucester County
- York County
- Isle of Wight County
- James City County

### Charlottesville / Central Virginia
Counties and cities commonly included:
- Charlottesville
- Albemarle County
- Greene County
- Fluvanna County
- Louisa County
- Nelson County

### Shenandoah Valley
Counties and cities commonly included:
- Winchester
- Staunton
- Waynesboro
- Harrisonburg
- Staunton
- Rockingham County
- Shenandoah County
- Frederick County
- Augusta County
- Rockbridge County

### Roanoke / Southwest Virginia
Counties and cities commonly included:
- Roanoke
- Salem
- Roanoke County
- Botetourt County
- Montgomery County
- Bedford County

### Southwest Virginia / Bristol
Counties and cities commonly included:
- Bristol
- Abingdon
- Wytheville
- Mount Airy (VA side)
- Smyth County
- Washington County
- Scott County

### Eastern Shore
Counties and cities commonly included:
- Accomack County
- Northampton County

## Sample ZIP code assignment strategy

A simple mapping strategy is to use ZIP code prefixes and county crosswalks:

- `220xx`, `201xx`, `201xx` → Northern Virginia
- `232xx`, `231xx`, `238xx` → Richmond Metro
- `234xx`, `235xx`, `236xx`, `237xx` → Hampton Roads
- `229xx` → Charlottesville / Central Virginia
- `240xx`, `241xx` → Roanoke / Southwest Virginia
- `226xx`, `228xx`, `244xx` → Shenandoah Valley
- `242xx`, `243xx`, `246xx` → Southwest Virginia / Bristol
- `233xx`, `234xx` (Eastern Shore side) → Eastern Shore

## Using a ZIP-to-region lookup file

For a reliable dataset, use a ZIP code crosswalk such as:

- U.S. Census ZCTA to county crosswalk
- Virginia Department of Transportation or state GIS ZIP boundary data
- Commercial ZIP code databases

Then add a `region` field for each ZIP code based on the county/metro area.

## Notes

- Region boundaries are approximate and may vary by source.
- Some ZIP codes cover multiple regions; choose the region that is most logical for your use case.
- This file is intended as a guide; a complete ZIP-to-region dataset should be built from an authoritative crosswalk.

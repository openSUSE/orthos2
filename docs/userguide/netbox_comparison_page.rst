**********************
NetBox Comparison Page
**********************

The concept of NetBox Comparisons was created to track the differences between a data model in Orthos 2 and NetBox at
the comparison point. This was introduced to help detect differences between Orthos 2 and NetBox records, before the
nightly pull-based data sync overwrites the data in Orthos2.

.. note:: Comparison results are deleted after two weeks at the moment to save space in the database.

.. note:: This page is only visible to you if you have administrator rights.

List View
#########

.. image:: ../img/userguide/20_netboxcomparison_list_view.png
  :alt: Orthos2 NetBox Comparison List View

This page provides a list of comparison runs between Orthos 2 and NetBox.

Quick Filter
############

.. image:: ../img/userguide/22_netboxcomparison_quick_filter.png
  :alt: Orthos2 NetBox Comparison Quick Filter

- All Object Types: Filter comparisons by object type (machine, network_interface, enclosure, etc.).
- From / To: Filter comparisons by the date range they were run in.
- Object Name Search: Search comparisons by (partial) object name.

Detail View
###########

.. image:: ../img/userguide/21_netboxcomparison_detail_view.png
  :alt: Orthos2 NetBox Comparison Detail View

This page provides a detail view of a single comparison for a single object.

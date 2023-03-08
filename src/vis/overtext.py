#!/usr/bin/env python3

import copy
import json
import argparse
import re

from flask import Flask

css = """<style>
/* Style the navbar */
#navbar {
  overflow: hidden;
  background-color: #333;
  z-index: 2;
}

/* Navbar links */
#navbar a {
  float: left;
  display: block;
  color: #f2f2f2;
  text-align: center;
  padding: 14px;
  text-decoration: none;
}

/* Page content */
.content {
  padding: 16px;
}

/* The sticky class is added to the navbar with JS when it reaches its scroll position */
.sticky {
  position: fixed;
  top: 0;
  width: 100%;
}

/* Add some top padding to the page content to prevent sudden quick movement (as the navigation bar gets a new position at the top of the page (position:fixed and top:0) */
.sticky + .content {
  padding-top: 60px;
}


.button {
  font: 15px;
  text-decoration: none;
  background-color: #EEEEEE;
  color: #333333;
  padding: 2px 6px 2px 6px;
  border-top: 1px solid #CCCCCC;
  border-right: 1px solid #333333;
  border-bottom: 1px solid #333333;
  border-left: 1px solid #CCCCCC;
}
.button:hover {
  background-color: #0075ff;
  color: white;
}


/* Tooltip container */
.tooltip {
  position: relative;
  display: inline-block;
  border-bottom: 1px dotted black;
}

.tooltip .tooltiptext {
  visibility: hidden;
  width: 500px;
  background-color: gray;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 5px;

  /* Position the tooltip */
  position: absolute;
  z-index: 1;
  bottom: 100%;
  left: 50%;
  margin-left: -250px;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
}

td {
  border-left: thin dotted white;
  border-right: thin dotted white;
  padding-left: 1em;
  padding-right: 1em;
  vertical-align: top;
  text-align: left;
}

th {
  padding-left: 1em;
  padding-right: 1em;
  white-space: nowrap;
  text-align: left;
}


.tablebestbutton {
  background-color: #e0eeff;
  color: black;
  border: 2px solid #0075ff;
  padding: 10px 20px;
  text-align: center;
  text-decoration: none;
  display: inline-block;
  font-size: 16px;
  cursor: pointer;
}
.tablebestbutton:hover {
  background-color: #0075ff;
  color: white;
}
.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.disabled:hover {
  opacity: 0.4;
  background-color: #e0eeff;
  color: black;
  border: 2px solid #0075ff;
}

</style>"""

# Misc notes:
# - Match columns have text set to nowrap, except if the text is more than 5
# tokens long. That accounts for cases like the 'Any' column.

def calc_overlap(val, comp, field):
    ctokens = val.split()
    ptokens = comp.split()
    if field[1] == 'right':
        ctokens.reverse()
        ptokens.reverse()
    count = 0
    for pos, (ctoken, ptoken) in enumerate(zip(ctokens, ptokens)):
        if ctoken.lower() == ptoken.lower():
            count += 1
        else:
            break
    return count

def grey_rows(rows, fields):
    # TODO: For each field, precompute:
    # - Which values are exact duplicates (and map to an ID, so we can just go down the list tracking which IDs have been seen)
    # - List of bigrams for each field
    # - 
    mod_rows = []
    seen = {}
    for row_no, (row, is_end_of_cluster) in enumerate(rows):
        nrow = []
        for field, val in enumerate(row.values):
            if val == '':
                nrow.append('')
                continue

            # TODO:
            # Precompute for the table:
            # - An ID for every value [then track seen IDs and see if this one is in it]
            #
            # Precompute for all pairs in the table:
            # - Longest match [then look up the pair of current and immediate previous]
            #
            # Plan for bigrams?
            # Plan for avoiding START - END repetition?

            # Check for duplicate
            is_duplicate = set()
            is_duplicate = seen.get(field, {}).get(val.lower(), set())
            seen.setdefault(field, {}).setdefault(val.lower(), set()).add(row_no)

            if len(is_duplicate) > 0:
                if row_no - 1 in is_duplicate:
                    val = "START_DUPLICATE{}END_DUPLICATE".format(val)
                else:
                    val = "START_FAR_DUPLICATE{}END_FAR_DUPLICATE".format(val)
            elif row_no > 0:
                # Do partial duplicates
                to_check = []
                to_check.append(row_no - 1)

                # Find longest match
                longest_near = 0
                longest_distant = 0
                for prev in to_check:
                    count = calc_overlap(val, rows[prev][0].values[field], fields[field])
                    if prev == row_no - 1:
                        longest_near = count
                    else:
                        longest_distant = max(longest_distant, count)
                if longest_distant > 0 or longest_near > 0:
                    tokens = val.split()
                    if fields[field][1] == 'right':
                        tokens.reverse()
                    for pos in range(max(longest_near, longest_distant)):
                        if pos < longest_near:
                            tokens[pos] = "START_DUPLICATE{}END_DUPLICATE".format(tokens[pos])
                        else:
                            tokens[pos] = "START_FAR_DUPLICATE{}END_FAR_DUPLICATE".format(tokens[pos])
                    if fields[field][1] == 'right':
                        tokens.reverse()
                    val = " ".join(tokens)

                # Find bigram matches
                if row_no > 0:
                    tokens = []
                    prev_tokens = rows[row_no - 1][0].values[field].lower().split()
                    prev_pairs = set()
                    for a, b in zip(prev_tokens, prev_tokens[1:]):
                        prev_pairs.add((a, b))
                    ctokens = val.split()
                    for pos, token in enumerate(ctokens):
                        if '_DUPLICATE' in token:
                            tokens.append(token)
                        elif pos+1 < len(ctokens) and (token.lower(), ctokens[pos+1].lower()) in prev_pairs:
                            tokens.append("START_FAR_DUPLICATE{}END_FAR_DUPLICATE".format(token))
                        elif pos > 0 and (ctokens[pos-1].lower(), token.lower()) in prev_pairs:
                            tokens.append("START_FAR_DUPLICATE{}END_FAR_DUPLICATE".format(token))
                        else:
                            tokens.append(token)
                    val = " ".join(tokens)

                tokens = val.split()
                for i, token in enumerate(tokens):
                    if i < len(tokens) - 1:
                        if token.endswith("END_DUPLICATE") and tokens[i+1].startswith("START_DUPLICATE"):
                            tokens[i] = token[:-len("END_DUPLICATE")]
                            tokens[i +1] = tokens[i+1][len("START_DUPLICATE"):]
                for i, token in enumerate(tokens):
                    if i < len(tokens) - 1:
                        if token.endswith("END_FAR_DUPLICATE") and tokens[i+1].startswith("START_FAR_DUPLICATE"):
                            tokens[i] = token[:-len("END_FAR_DUPLICATE")]
                            tokens[i +1] = tokens[i+1][len("START_FAR_DUPLICATE"):]
                val = ' '.join(tokens)
            nrow.append(val)

        mod_rows.append((row, nrow, is_end_of_cluster))
    return mod_rows

def sort_rows(rows, sort_column):
    # Group by values in the sort column
    groups = {}
    for row in rows:
        content = row.values[sort_column]
        #groups.setdefault(content, []).append(row)
        groups.setdefault("single", []).append(row)
    singletons = [(value, g[0]) for value, g in groups.items() if len(g) == 1]
    singletons.sort()
    sorted_groups = [(len(g), g) for _, g in groups.items() if len(g) > 1]
    sorted_groups.sort(reverse=True)

    # Sort groups by column to the right, then column to the left
    final_rows = []
    for _, group in sorted_groups:
        keys = [v for v in range(sort_column, len(rows[0].values))] + [v for v in range(sort_column - 1, -1, -1)]
        group.sort(key=lambda x: [x.values[k] for k in keys])
        final_rows += group

    final_rows += [v[1] for v in singletons]

    return final_rows

def default_table_config(tables):
    table_config_dict = {}
    for table in tables:
        name = table.name
        show_elsewhere = False
        merge_level = table.default_agg
        sort_column = 1
        table_config_dict[name] = {
            'show_elsewhere': show_elsewhere,
            'merge_level': merge_level,
            'sort_column': sort_column,
        }
    return table_config_dict

def decode_table_config(table_config, tables):
    if table_config == '':
        return default_table_config(tables)
    parts = table_config.split(';')
    table_config_dict = {}
    pos = 0
    while pos < len(parts):
        name = parts[pos]
        pos += 1
        show_elsewhere = parts[pos] in ['True', 'true']
        pos += 1
        merge_level = int(parts[pos])
        pos += 1
        sort_column = int(parts[pos])
        pos += 1
        table_config_dict[name] = {
            'show_elsewhere': show_elsewhere,
            'merge_level': merge_level,
            'sort_column': sort_column,
        }
    return table_config_dict

def encode_table_config(table_config_dict):
    parts = []
    for name, values in table_config_dict.items():
        parts.append(name)
        parts.append(str(values['show_elsewhere']))
        parts.append(str(values['merge_level']))
        parts.append(str(values['sort_column']))
    return ';'.join(parts)

def make_url(table_config_dict, change, dataset_name, table_id):
    nconfig = copy.deepcopy(table_config_dict)
    for name, fields in change.items():
        for field, value in fields.items():
            nconfig[name][field] = value

    encoded = encode_table_config(nconfig)
    return '/overtext/{}/{}/#{}-title'.format(dataset_name, encoded, table_id)

def make_page(dataset, dataset_names, dataset_name, table_config):
    tables = dataset['tables']
    table_config_dict = decode_table_config(table_config, tables)

    html_tables = []
    html_tables.append('<div id="navbar">')
    for table_id, table in enumerate(tables):
        html_tables.append('<a href="#{}-title">{}</a>'.format(table_id, table.name))
    html_tables.append('</div>')
           
    scripts = ["""
// When the user scrolls the page, execute myFunction
window.onscroll = function() {myFunction()};

// Get the navbar
var navbar = document.getElementById("navbar");

// Get the offset position of the navbar
var sticky = navbar.offsetTop;

// Add the sticky class to the navbar when you reach its scroll position. Remove "sticky" when you leave the scroll position
function myFunction() {
if (window.pageYOffset >= sticky) {
navbar.classList.add("sticky")
} else {
navbar.classList.remove("sticky");
}
}
"""]

    for table_id, table in enumerate(tables):
        config = table_config_dict[table.name]
        merge_level = config['merge_level']
        table_best = config['show_elsewhere']

        html = [
            '<div style="padding:50px" id="{}-title">'.format(table_id),
            '<h3 style="text-align: center;">{} Table</h3>'.format(" ".join(table.name.split("-"))),
        ]

        # Button to show / hide table-best

        html += [
            '    <div style="text-align: center; padding:10px">',
            '        <a class="button{}" href="{}">Hide rows shown elsewhere</a>'.format(" disabled" if not table_best else "", make_url(table_config_dict, {table.name: {"show_elsewhere": False}}, dataset_name, table_id)),
            '        <a class="button{}" href="{}">Show rows shown elsewhere</a>'.format(" disabled" if table_best else "", make_url(table_config_dict, {table.name: {"show_elsewhere": True}}, dataset_name, table_id)),
            '    </div>',
        ]

        # Work out merge levels for this table
        if len(table.agg) > 1:
            html += [
                '    <div style="text-align: center; padding:10px">',
                '        <a class="button{}" href="{}">Show smallest clusters</a>'.format(" disabled" if merge_level == 0 else "", make_url(table_config_dict, {table.name: {"merge_level": 0}}, dataset_name, table_id)),
                '        <a class="button{}" href="{}">Show smaller clusters</a>'.format(" disabled" if merge_level == 0 else "", make_url(table_config_dict, {table.name: {"merge_level": max(0, merge_level - 1)}}, dataset_name, table_id)),
                '        <a class="button{}" href="{}">Show larger clusters</a>'.format(" disabled" if merge_level == len(table.agg) - 1 else "", make_url(table_config_dict, {table.name: {"merge_level": min(len(table.agg) - 1, merge_level + 1)}}, dataset_name, table_id)),
                '        <a class="button{}" href="{}">Show single cluster</a>'.format(" disabled" if merge_level == len(table.agg) - 1 else "", make_url(table_config_dict, {table.name: {"merge_level": len(table.agg) - 1}}, dataset_name, table_id)),
                '    </div>',
            ]

        visible = 'block' 
        html += [
            '<table frame="box" rules="cols" id="table{}-{}-{}" style="border: 1px solid white; display:{}">'.format(table_id, merge_level, table_best, visible),
        ]

        # Do header
        html.append("    <tr>")
        for field_no, (field, alignment) in enumerate(table.fields):
            if alignment == 'hidden':
                continue
            if 'Other' in field:
                field = ''

            field += ' <a class="{}" href="{}">&#x25BC;</a>'.format("disabled" if field_no == config['sort_column'] else "", make_url(table_config_dict, {table.name: {"sort_column": field_no}}, dataset_name, table_id))
            if alignment == 'left':
                html.append('      <th>{}</th>'.format(field))
            else:
                html.append('      <th style="text-align: {};">{}</th>'.format(alignment, field))

        html.append("    </tr>")
        html.append("  </thead>")

        # Sorting TODO: ignore caps
        # Links TODO: do not recolour if clicked
        # Sorting: have a small button for secondary sort
        # Make sure secondary sort does the reverse tokens where appropriate
        # Show singletons, but put them at the bottom
        # Sort clusters by cohesiveness

        # TODO: Other vis
        # TODO: Other data
        # TODO: YouTube data

        # Do rows
        html.append("  <tbody>")

        # Sort rows
        all_groups = []
        for cluster in table.agg[merge_level]:
            # Get rows for this cluster
            current_rows = []
            for row_id in cluster:
                use = table.rows[row_id].best_type == "GlobalBest"
                if table_best and table.rows[row_id].best_type == "TableBest":
                    use = True
                if use:
                    current_rows.append(table.rows[row_id])

            # Sort based on the column selected
            sort_column = config['sort_column']
            current_rows = sort_rows(current_rows, sort_column)

            # Add to clustered rows
            all_groups.append([(row, row == current_rows[-1]) for row in current_rows])
        # Sort clusters
        all_rows = []
        all_groups.sort(key=lambda x: len(x))
        for group in all_groups:
            all_rows += group
    
        # Calculate grey
        all_rows = grey_rows(all_rows, table.fields)

        # Render
        for pos, (row, row_values, is_end_of_cluster) in enumerate(all_rows):
            add_separator = ''
            if is_end_of_cluster and pos != len(all_rows) - 1:
                add_separator = " style='border-bottom: thin dotted gray;'"
            html.append("    <tr{}>".format(add_separator))
            for pos, content in enumerate(row_values):
                if table.fields[pos][1] == 'hidden':
                    continue
                if len(content) == 0:
                    html.append("      <td></td>")
                    continue
                if table.fields[pos][1] == 'left':
                    start = '      <td>'
                else:
                    start = '      <td style="text-align: {};">'.format(table.fields[pos][1])
                end = '</td>'

                # Format
                # Apply edit to de-emphasise items
                content = '<span style="color:#e3e3e3">'.join(content.split("START_DUPLICATE"))
                content = '</span>'.join(content.split("END_DUPLICATE"))
                content = '<span style="color:#b0b0b0">'.join(content.split("START_FAR_DUPLICATE"))
                content = '</span>'.join(content.split("END_FAR_DUPLICATE"))
                if 'Other' not in table.fields[pos][0] or pos == 1:
                    if len(row_values[pos].split()) < 6:
                        if 'span style' in content:
                            content = 'style="white-space: nowrap; '.join(content.split('style="'))
                        else:
                            content = '<span style="white-space: nowrap;">'.join(content.split('<span>'))
                    if row.multi_sentence:
                        if '<span' not in content:
                            content = '<span>{}</span>'.format(content)
                        content = '<div class="tooltip">' + content + '<span class="tooltiptext">{} <i>{}</i> {}</span></div>'.format(row.context[0], row.sentence, row.context[1])

                # Combine
                html.append(start + content + end)
            html.append("    </tr>")
        html.append("  </tbody>")
        html.append("</table>")


        html.append("</div>")


        html_tables.append("\n".join(html))


    parts = [
        "<!DOCTYPE html>",
        "<html>",
        css,
        "<body>", 
        '\n'.join(html_tables),
        "</body>",
        "<script>",
        '\n'.join(scripts),
        "</script>",
        "</html>"
    ]
    return '\n'.join(parts)

def calculate_cluster_cohesion(rows, sim_scores):
    pair_sim = []
    for row0 in rows:
        for row1 in rows:
            if row0 == row1:
                break
            doc_id0 = row0[-1][0][0]
            doc_id1 = row1[-1][0][0]
            pair_sim.append(sim_scores[doc_id0, doc_id1])
    pair_sim.sort()
    # Return the score for the least similar pair
    if len(pair_sim) == 0:
        return 0
    return pair_sim[0]


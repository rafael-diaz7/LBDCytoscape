import py4cytoscape as p4c
import node_edge as ne
import numpy as np
import pandas as pd
import codecs
import time
import re
import os


def tree_to_txt(tree):
    """
    converts .tree to .txt with " " delimiter
    :param tree: name of the file with no extension, MUST BE A ".tree" file
    :return: none -> creates new file
    """
    with open(tree + '.tree') as file:
        wrt = open(tree + '_edges.csv', 'w')
        lines = file.readlines()
        wrt.writelines(lines)
        wrt.close()


def clusters_to_csv(clusters):
    """
    converts .clusters to .csv with "\t" delimiter
    :param clusters: name of file with no extension, MUST BE A ".clusters" file
    :return: none -> creates new file
    """
    block_size = 1048576
    with codecs.open(clusters + '.clusters', "r", "windows-1252") as sourceFile:
        with codecs.open('dump.txt', "w", "utf-8") as targetFile:
            while True:
                contents = sourceFile.read(block_size)
                if not contents:
                    break
                targetFile.write(contents)
        targetFile.close()

    with open('dump.txt') as file:
        wrt = open(clusters + '_nodes.csv', 'w')
        for i in file:
            split_list = re.findall(r"(\d+) - (.*) - (\d+: .*)", i)[0]
            wrt.write(split_list[0] + "\t" + split_list[1] + "\t" + split_list[2] + "\n")
        wrt.close()

    os.remove('dump.txt')


def clean_data(project_name):
    nodes = pd.read_csv(project_name + '_nodes.csv', delimiter='\t', names=['id', 'name', 'size'])
    # nodes['id'] = nodes.id.astype(str)

    sizes = []
    ifs = []
    for i in nodes['size']:
        sep = i.split(':')
        sizes.append(int(sep[0]))
        # sizes.append(np.log(int(sep[0]) + 1) ** 2)
        ifs.append(sep[1])

    nodes['size'] = pd.Series(sizes)
    nodes['info'] = pd.Series(ifs)
    nodes = nodes.sort_values('id')

    edges = pd.read_csv(project_name + '_edges.csv', delimiter=' ', names=['source', 'n1', 'n2'])
    edges['target'] = edges.index
    del edges['n1']
    del edges['n2']
    # edges['source'] = edges.index.astype(str)
    # edges['target'] = edges.target.astype(str)
    edges = edges[:-1]
    edges = edges.sort_values('source')

    nodes.to_csv(project_name + '_nodes.csv')
    edges.to_csv(project_name + '_edges.csv')


def width_recurse(node):
    """

    :param node:
    :return:
    """
    if node is None:
        return 0
    elif node.get_c1() is None and node.get_c2() is None:
        node.set_parent_edge_width(node.get_weight())
        return node.get_weight()
    elif node.get_c2() is None:
        num = width_recurse(node.get_c1().get_child())
        node.set_parent_edge_width(num)
        return num
    else:
        num = width_recurse(node.get_c1().get_child()) + width_recurse(node.get_c2().get_child())
        node.set_parent_edge_width(num)
        return num


def edge_color_recurse(node):
    if node is None or (node.get_c1() is None and node.get_c2() is None):
        return 0
    elif node.get_c2() is None:
        node.get_c1().get_child().set_parent_edge_color('#0000FF')
    else:
        if node.get_c1().get_child().get_parent_edge_width() > node.get_c2().get_child().get_parent_edge_width():
            node.get_c1().get_child().set_parent_edge_color('#0000FF')
            node.get_c2().get_child().set_parent_edge_color('#FFA500')
        elif node.get_c1().get_child().get_parent_edge_width() < node.get_c2().get_child().get_parent_edge_width():
            node.get_c2().get_child().set_parent_edge_color('#0000FF')
            node.get_c1().get_child().set_parent_edge_color('#FFA500')
        else:
            node.get_c1().get_child().set_parent_edge_color('#FFC0CB')
            node.get_c2().get_child().set_parent_edge_color('#FFC0CB')
        edge_color_recurse(node.get_c1().get_child())
        edge_color_recurse(node.get_c2().get_child())


def create_width(project_name):
    nodes = pd.read_csv(project_name + '_nodes.csv')
    edges = pd.read_csv(project_name + '_edges.csv')

    id = nodes['id'].tolist()
    size = nodes['size'].tolist()

    all_nodes = {}  # make dict
    for i in range(len(id)):
        all_nodes[id[i]] = (ne.Node(id[i], size[i]))

    source = edges['source'].tolist()
    target = edges['target'].tolist()

    all_edges = []
    for i in range(len(source)):
        if source[i] in all_nodes.keys() and target[i] in all_nodes.keys():
            edge = ne.Edge(all_nodes[source[i]], all_nodes[target[i]])
            all_edges.append(edge)
            if all_nodes[source[i]].get_c1() is None:
                all_nodes[source[i]].set_c1(edge)
            else:
                all_nodes[source[i]].set_c2(edge)
        else:
            quit("Source or target node not defined")
    width_recurse(all_nodes[len(id)-1])
    edge_widths = []
    for i in all_nodes.values():
        edge_widths.append(i.get_parent_edge_width())
        # edge_widths.append(np.log(i.get_parent_edge_width()))
    # edge_widths = edge_widths[:-1]
    edges = edges.sort_values('target')
    edges['width'] = edge_widths[:-1]

    edge_color_recurse(all_nodes[len(id)-1])
    colors = []
    for i in all_nodes.values():
        colors.append(i.get_parent_edge_color())
    edges['color'] = colors[:-1]
    edges.to_csv(project_name + '_edges.csv')


def graph_to_cyto(project_name):
    """

    :param project_name:
    :return:
    """
    start = time.time()

    nodes = pd.read_csv(project_name + '_nodes.csv')
    edges = pd.read_csv(project_name + '_edges.csv')

    nodes['id'] = nodes.id.astype(str)
    nodes['font'] = nodes['size'].map(lambda x: x / 3)
    nodes.at[len(nodes['id'].tolist()) - 1, 'name'] = 'root'

    edges['source'] = edges['source'].astype(str)
    edges['target'] = edges['target'].astype(str)

    p4c.create_network_from_data_frames(nodes, edges, title="lbd_test", collection="tests")
    p4c.set_node_shape_default('ELLIPSE')
    p4c.set_node_color_default('#00FF00')
    p4c.set_node_size_mapping('id', nodes['id'].tolist(), nodes['size'].tolist(), mapping_type='d')
    p4c.set_node_font_size_mapping('name', nodes['name'].tolist(), nodes['font'].tolist(), mapping_type='d')
    p4c.set_edge_line_width_bypass(p4c.get_all_edges(), edges['width'].tolist())
    p4c.set_edge_color_bypass(p4c.get_all_edges(), edges['color'].tolist())
    p4c.set_node_shape_bypass(['root'], 'HEXAGON')
    p4c.set_node_color_bypass(['root'], '#FF0000')

    end = time.time()

    nodes.to_csv('x.csv')
    edges.to_csv('y.csv')
    print("time taken in seconds:", end - start)
    print("time in minutes:", (end - start) / 60)


if __name__ == "__main__":
    # project = input("Please enter the name of your files without the extension, case sensitive. (ex - cardiacArrestDise"
    #                 "ases): ")
    project = "1983_1985_window8_v"
    clusters_to_csv(project)
    tree_to_txt(project)
    clean_data(project)
    create_width(project)
    graph_to_cyto(project)

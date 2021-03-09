def mergeSort(x):
    """Take an array and sort it using merge sort."""

    if len(x) < 2:
        return x
    if len(x) == 2:
        # if there are only two elements, just need to make one comparison
        return [x[0], x[1]] if x[0] < x[1] else [x[1], x[0]]

    # recursively sort the first half and then second half
    arr1 = mergeSort(x[:len(x) // 2])
    arr2 = mergeSort(x[len(x) // 2:])

    res = []

    # merge the two sorted arrays
    while arr1 and arr2:
        if arr1[0] < arr2[0]:
            res.append(arr1.pop(0))
        else:
            res.append(arr2.pop(0))

    res += arr1 + arr2

    return res


def quickSort(x):
    """Take an array and sort it using quick sort."""

    if len(x) < 2:
        return x

    less = []
    more = []

    # select first element as pivot
    equal = [x[0]]

    for i in range(1, len(x)):
        if x[i] < x[0]:
            less.append(x[i])
        elif x[i] == x[0]:
            equal.append(x[i])
        else:
            more.append(x[i])

    return quickSort(less) + equal + quickSort(more)

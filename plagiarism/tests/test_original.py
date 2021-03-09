def mergeSort(num):
    """Take an array and sort it using merge sort."""

    if len(num) < 2:
        return num
    if len(num) == 2:
        # if there are only two elements, just need to make one comparison
        return [num[0], num[1]] if num[0] < num[1] else [num[1], num[0]]

    # recursively sort the first half and then second half
    arr1 = mergeSort(num[:len(num) // 2])
    arr2 = mergeSort(num[len(num) // 2:])

    res = []

    # merge the two sorted arrays
    while arr1 and arr2:
        if arr1[0] < arr2[0]:
            res.append(arr1.pop(0))
        else:
            res.append(arr2.pop(0))

    res += arr1 + arr2

    return res


def quickSort(num):
    """Take an array and sort it using quick sort."""

    if len(num) < 2:
        return num

    less = []
    more = []

    # select first element as pivot
    equal = [num[0]]

    for i in range(1, len(num)):
        if num[i] < num[0]:
            less.append(num[i])
        elif num[i] == num[0]:
            equal.append(num[i])
        else:
            more.append(num[i])

    return quickSort(less) + equal + quickSort(more)

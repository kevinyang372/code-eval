def mergeSort(nums):
    N = len(nums)
    # split
    if N < 2:
        return nums

    left, right = nums[:N // 2], nums[N // 2:]

    # sub
    left = mergesort(left)
    right = mergesort(right)

    # combine
    ret = []
    while left and right:
        if left[0] <= right[0]:
            ret.append(left.pop(0))
        else:
            ret.append(right.pop(0))

    for rem in (left, right):
        if rem:
            ret += rem

    return ret


def quickSort(array):
    """Sort the array by using quicksort."""

    less = []
    equal = []
    greater = []

    if len(array) > 1:
        pivot = array[0]
        for x in array:
            if x < pivot:
                less.append(x)
            elif x == pivot:
                equal.append(x)
            elif x > pivot:
                greater.append(x)
        # Don't forget to return something!
        return sort(less) + equal + sort(greater)  # Just use the + operator to join lists
    # Note that you want equal ^^^^^ not pivot
    else:  # You need to handle the part at the end of the recursion - when you only have one element in your array, just return the array.
        return array

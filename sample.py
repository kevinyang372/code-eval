def bubble_sort(nums):
    """Bubble_sort"""
    for i in range(len(nums) - 1):
        for j in range(len(nums) - i - 1):
            if nums[j] > nums[j + 1]:
                nums[j], nums[j + 1] = nums[j + 1], nums[j]
    return nums


def selection_sort(nums):
    for i in range(len(nums)):
        min_val = nums[i]
        min_ind = i
        for t in range(i + 1, len(nums)):
            if min_val > nums[t]:
                min_ind = t
                min_val = nums[t]

        nums[i], nums[min_ind] = nums[min_ind], nums[i]

    return nums

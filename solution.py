
def sum_primes_up_to_n(n):
    """
    Finds the sum of all prime numbers up to a given integer n using the Sieve of Eratosthenes.

    Args:
        n (int): The upper limit (inclusive) to find prime numbers.

    Returns:
        int: The sum of all prime numbers up to n.
             Returns 0 if n is less than 2.
    """
    if n < 2:
        return 0

    # Create a boolean array "is_prime[0..n]" and initialize
    # all entries it as true. A value in is_prime[i] will
    # finally be false if i is Not a prime, else true.
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False  # 0 and 1 are not prime numbers

    p = 2
    while (p * p <= n):
        # If is_prime[p] is still true, then it is a prime
        if is_prime[p]:
            # Update all multiples of p
            for multiple in range(p * p, n + 1, p):
                is_prime[multiple] = False
        p += 1

    # Sum all prime numbers
    total_sum = 0
    for i in range(2, n + 1):
        if is_prime[i]:
            total_sum += i

    return total_sum

/*
 * Check decoding of prctl PR_GET_PDEATHSIG/PR_SET_PDEATHSIG operations.
 *
 * Copyright (c) 2016 JingPiao Chen <chenjingpiao@foxmail.com>
 * Copyright (c) 2016 Eugene Syromyatnikov <evgsyr@gmail.com>
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. The name of the author may not be used to endorse or promote products
 *    derived from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
 * IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
 * IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
 * NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
 * THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "tests.h"
#include <asm/unistd.h>
#include <linux/prctl.h>

#if defined __NR_prctl && defined PR_GET_PDEATHSIG && defined PR_SET_PDEATHSIG

# include <stdio.h>
# include <unistd.h>
# include <sys/signal.h>

# include "kernel_types.h"

int
main(void)
{
	static const kernel_ulong_t bogus_signal =
		(kernel_ulong_t) 0xbadc0deddeadfeedULL;

	int *pdeathsig = tail_alloc(sizeof(*pdeathsig));
	long rc;

	rc = syscall(__NR_prctl, PR_SET_PDEATHSIG, bogus_signal);
	printf("prctl(PR_SET_PDEATHSIG, %llu) = %s\n",
	       (unsigned long long) bogus_signal, sprintrc(rc));

	rc = syscall(__NR_prctl, PR_SET_PDEATHSIG, SIGINT);
	printf("prctl(PR_SET_PDEATHSIG, SIGINT) = %s\n", sprintrc(rc));

	rc = syscall(__NR_prctl, PR_GET_PDEATHSIG, NULL);
	printf("prctl(PR_GET_PDEATHSIG, NULL) = %s\n", sprintrc(rc));

	rc = syscall(__NR_prctl, PR_GET_PDEATHSIG, pdeathsig + 1);
	printf("prctl(PR_GET_PDEATHSIG, %p) = %s\n",
	       pdeathsig + 1, sprintrc(rc));

	rc = syscall(__NR_prctl, PR_GET_PDEATHSIG, pdeathsig);
	if (rc) {
		printf("prctl(PR_GET_PDEATHSIG, %p) = %s\n",
		       pdeathsig, sprintrc(rc));
	} else {
		printf("prctl(PR_GET_PDEATHSIG, [SIGINT]) = %s\n",
		       sprintrc(rc));
	}

	puts("+++ exited with 0 +++");
	return 0;
}

#else

SKIP_MAIN_UNDEFINED("__NR_prctl && PR_GET_PDEATHSIG && PR_SET_PDEATHSIG")

#endif

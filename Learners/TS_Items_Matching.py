import numpy as np
import matching_lp as lp
np.random.seed(1234)


class TS_Items_Matching():
    def __init__(self, margins_item1, margins_item2, daily_customers, discounts, promo_fractions):
        self.t = 0
        self.beta_parameters_item1 = np.ones((len(margins_item1), 4, 2))
        self.beta_parameters_item2 = np.ones((len(margins_item2), 4, 4, 2))

        self.margins_item1 = margins_item1
        self.margins_item2 = margins_item2
        self.daily_customers = daily_customers
        self.discounts = discounts
        self.promo_fractions = promo_fractions

    def pull_arm(self):
        # Computing the upper_conf total revenue for each pair of margins, along with the corresponding matching matrix.
        # Note that the conversion rates for the two items are the learned ones (extracted from the Beta distributions)
        value = np.zeros((len(self.margins_item1), len(self.margins_item2)))
        matching = np.zeros((len(self.margins_item1), len(self.margins_item2), 4, 4))

        for margin1 in range(len(self.margins_item1)):
            beta_item1 = np.random.beta(self.beta_parameters_item1[margin1, :, 0], self.beta_parameters_item1[margin1, :, 1])
            for margin2 in range(len(self.margins_item2)):
                beta_item2 = np.random.beta(self.beta_parameters_item2[margin2, :, :, 0], self.beta_parameters_item2[margin2, :, :, 1])
                daily_promos = (self.promo_fractions * sum(self.daily_customers * beta_item1)).astype(int)
                reward_item2, matching[margin1][margin2] = lp.matching_lp(self.margins_item2[margin2], self.discounts, beta_item2, daily_promos, (self.daily_customers * beta_item1).astype(int))
                value[margin1][margin2] = self.margins_item1[margin1] * (self.daily_customers * beta_item1).sum() + reward_item2

        # Selecting the indices of the maximum of the upper_conf matrix (breaking ties randomly)
        # and the corresponding matching matrix
        arm_flat = np.argmax(np.random.random(value.shape) * (value == np.amax(value, None, keepdims=True)), None)
        arm = np.unravel_index(arm_flat, value.shape)

        return arm, matching[arm[0]][arm[1]]

    # Pulled_arm contains the indices of the two pulled arms (pulled_arm[0] and pulled_arm[1]).
    # Reward contains the array of conversion rates for the first item (reward[0]), the matrix of conversion rates for
    # the second item (reward[1]) obtained from the environment.
    def update(self, pulled_arm, reward):
        self.t += 1

        self.beta_parameters_item1[pulled_arm[0], :, 0] = self.beta_parameters_item1[pulled_arm[0], :, 0] + reward[0]
        self.beta_parameters_item1[pulled_arm[0], :, 1] = self.beta_parameters_item1[pulled_arm[0], :, 1] + 1.0 - reward[0]

        self.beta_parameters_item2[pulled_arm[1], :, :, 0] = self.beta_parameters_item2[pulled_arm[1], :, :, 0] + reward[1]
        self.beta_parameters_item2[pulled_arm[1], :, :, 1] = self.beta_parameters_item2[pulled_arm[1], :, :, 1] + 1.0 - reward[1]
